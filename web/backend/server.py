"""FastAPI backend for the CLERIC research pipeline.

Exposes a REST + WebSocket API that starts research jobs, streams live
progress to connected clients, and serves completed results.
"""

from __future__ import annotations

import logging
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path setup — allow importing the cleric package from the project root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from cleric.config import Config  # noqa: E402
from cleric.orchestrator import PipelineResult, ResearchPipeline  # noqa: E402
from cleric.output.mermaid import MermaidGenerator  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("cleric.api")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CLERIC Research API",
    description="Web API for the C.L.E.R.I.C. multi-agent research pipeline.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------
# Each job is a dict with keys:
#   status: "pending" | "running" | "complete" | "error"
#   result: dict | None          (PipelineResult.to_dict() on completion)
#   events: list[dict]           (chronological stream events)
#   mermaid_diagrams: dict       ({diagram_name: mermaid_content})
#   error: str | None
jobs: dict[str, dict[str, Any]] = {}

# Active WebSocket connections keyed by job_id.
# Multiple clients can watch the same job.
_ws_connections: dict[str, list[WebSocket]] = {}
_ws_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CONTENT_TRUNCATE_LIMIT = 5000


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class ResearchRequest(BaseModel):
    query: str


class ResearchResponse(BaseModel):
    job_id: str


class JobStatus(BaseModel):
    status: str
    result: dict | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate(text: str, limit: int = _CONTENT_TRUNCATE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[...truncated]"


def _push_event(job_id: str, event: dict) -> None:
    """Append an event to the job's event log and broadcast to WebSocket clients."""
    if job_id in jobs:
        jobs[job_id]["events"].append(event)

    with _ws_lock:
        sockets = list(_ws_connections.get(job_id, []))

    for ws in sockets:
        try:
            # We are in a background thread so we cannot ``await``.
            # FastAPI/Starlette WebSocket objects expose a sync-compatible
            # ``send_json`` only inside an async context. Instead we enqueue
            # via the event loop that owns the socket.
            import asyncio

            loop = _get_ws_loop(ws)
            if loop is not None and loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_json(event), loop)
        except Exception:
            logger.debug("Failed to push event to WebSocket for job %s", job_id)


def _get_ws_loop(ws: WebSocket) -> Any:
    """Retrieve the asyncio event loop that owns *ws*."""
    # Starlette stores the ASGI scope/state on the WebSocket; the event loop
    # is available via the running server thread.  We stash it during the
    # handshake (see the /ws endpoint).
    return getattr(ws, "_cleric_loop", None)


def _generate_mermaid_diagrams(result: PipelineResult) -> dict[str, str]:
    """Run MermaidGenerator and read back the generated files as strings."""
    config = Config.from_env()
    output_dir = config.output_dir / "mermaid"
    generator = MermaidGenerator(str(output_dir))

    try:
        file_map: dict[str, Path] = generator.generate_all(result)
    except Exception:
        logger.exception("Mermaid diagram generation failed")
        return {}

    diagrams: dict[str, str] = {}
    for name, filepath in file_map.items():
        try:
            diagrams[name] = filepath.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Could not read mermaid file %s", filepath)
    return diagrams


# ---------------------------------------------------------------------------
# Pipeline runner (executed in a background thread)
# ---------------------------------------------------------------------------
def _run_pipeline(job_id: str, query: str) -> None:
    """Execute the research pipeline, emitting events as stages progress."""
    jobs[job_id]["status"] = "running"

    try:
        config = Config.from_env()
        pipeline = ResearchPipeline(config)

        # Wire up callbacks ------------------------------------------------
        def on_start(stage: str) -> None:
            event = {
                "type": "stage_start",
                "stage": stage,
                "timestamp": _now_iso(),
            }
            _push_event(job_id, event)

        def on_complete(stage: str, agent_result: Any) -> None:
            event = {
                "type": "stage_complete",
                "stage": stage,
                "data": {
                    "agent_name": agent_result.agent_name,
                    "role": agent_result.role,
                    "content": _truncate(agent_result.content),
                    "structured_data": agent_result.data,
                    "tool_call_count": len(agent_result.tool_calls_made),
                    "tokens": agent_result.tokens_used,
                },
                "tokens": agent_result.tokens_used,
                "timestamp": _now_iso(),
            }
            _push_event(job_id, event)

        pipeline.on_stage_start(on_start)
        pipeline.on_stage_complete(on_complete)

        # Run --------------------------------------------------------------
        result: PipelineResult = pipeline.run(query)

        # Generate Mermaid diagrams ----------------------------------------
        mermaid_diagrams = _generate_mermaid_diagrams(result)
        jobs[job_id]["mermaid_diagrams"] = mermaid_diagrams

        # Build final result payload ---------------------------------------
        result_dict = result.to_dict()
        result_dict["mermaid_diagrams"] = mermaid_diagrams

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["result"] = result_dict

        complete_event = {
            "type": "pipeline_complete",
            "result": result_dict,
            "timestamp": _now_iso(),
        }
        _push_event(job_id, complete_event)

    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(exc)

        error_event = {
            "type": "error",
            "message": str(exc),
            "timestamp": _now_iso(),
        }
        _push_event(job_id, error_event)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple liveness / readiness probe."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest) -> ResearchResponse:
    """Start a new research job.

    Returns a ``job_id`` that can be used to connect via WebSocket or poll
    for results.
    """
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "pending",
        "result": None,
        "events": [],
        "mermaid_diagrams": {},
        "error": None,
    }

    thread = threading.Thread(
        target=_run_pipeline,
        args=(job_id, request.query),
        name=f"pipeline-{job_id[:8]}",
        daemon=True,
    )
    thread.start()

    logger.info("Started research job %s for query: %s", job_id, request.query[:120])
    return ResearchResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Return the current status (and result if complete) of a research job."""
    job = jobs.get(job_id)
    if job is None:
        return JobStatus(status="not_found")

    return JobStatus(
        status=job["status"],
        result=job["result"],
        error=job["error"],
    )


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws/{job_id}")
async def websocket_progress(ws: WebSocket, job_id: str) -> None:
    """Stream live pipeline progress events for a research job.

    On connect the server replays any events that were already emitted
    before the client joined, then continues streaming in real time until
    the pipeline completes (or errors).
    """
    await ws.accept()

    job = jobs.get(job_id)
    if job is None:
        await ws.send_json({"type": "error", "message": "Job not found", "timestamp": _now_iso()})
        await ws.close()
        return

    # Stash the event loop so the background thread can push events.
    import asyncio

    ws._cleric_loop = asyncio.get_running_loop()  # type: ignore[attr-defined]

    # Register this socket.
    with _ws_lock:
        _ws_connections.setdefault(job_id, []).append(ws)

    try:
        # Replay events the client missed.
        for event in list(job["events"]):
            await ws.send_json(event)

        # Keep the socket open until the client disconnects or the job ends.
        # We rely on the background thread to push new events via
        # ``_push_event``.  Here we just keep reading (to detect disconnect).
        while True:
            # ``receive_text`` blocks until the client sends something or
            # disconnects.  We don't expect client messages, but we need to
            # keep the coroutine alive.
            await ws.receive_text()

    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected from job %s", job_id)
    finally:
        with _ws_lock:
            conns = _ws_connections.get(job_id, [])
            if ws in conns:
                conns.remove(ws)
            if not conns:
                _ws_connections.pop(job_id, None)
