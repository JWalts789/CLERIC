"""Launch the CLERIC API server."""

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def load_demo_data():
    """Load sample outputs into the SQLite store for demo purposes."""
    from db import ResultStore

    project_root = Path(__file__).resolve().parent.parent.parent
    store = ResultStore(str(project_root / "data" / "cleric.db"))
    samples_dir = project_root / "docs" / "samples"

    if not samples_dir.exists():
        print("No samples directory found — skipping demo data.")
        return

    loaded = 0
    for sample_dir in samples_dir.iterdir():
        if not sample_dir.is_dir():
            continue

        raw_json = sample_dir / "raw_data.json"
        if not raw_json.exists():
            continue

        data = json.loads(raw_json.read_text(encoding="utf-8"))
        job_id = f"demo-{uuid.uuid4().hex[:8]}"

        # Collect mermaid diagrams
        mermaid_diagrams = {}
        for mermaid_file in sample_dir.glob("*.mermaid"):
            name = mermaid_file.stem.split("_", 1)[-1] if "_" in mermaid_file.stem else mermaid_file.stem
            mermaid_diagrams[name] = mermaid_file.read_text(encoding="utf-8")

        store.save_result(
            job_id=job_id,
            query=data.get("query", sample_dir.name),
            result_dict=data,
            mermaid_dict=mermaid_diagrams,
        )
        loaded += 1
        print(f"  Loaded demo: {data.get('query', sample_dir.name)[:60]}")

    print(f"Demo mode: loaded {loaded} sample result(s) into history.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch the CLERIC API server.")
    parser.add_argument("--demo", action="store_true", help="Load sample outputs into history for demo purposes")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()

    if args.demo:
        load_demo_data()

    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=args.port, reload=True)
