"""Tests for cleric.output.report.ReportGenerator."""

from pathlib import Path

import pytest

from cleric.agents.base import AgentResult
from cleric.orchestrator import PipelineResult
from cleric.output.report import ReportGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_result(name: str, role: str, content: str = "", data: dict | None = None) -> AgentResult:
    return AgentResult(
        agent_name=name,
        role=role,
        content=content,
        data=data or {},
        tool_calls_made=[{"tool": "web_search", "input": {"query": "test"}, "result_preview": "..."}],
        tokens_used={"input": 100, "output": 50},
    )


def _make_pipeline_result() -> PipelineResult:
    return PipelineResult(
        query="What causes climate change?",
        timestamp="2026-01-01T00:00:00Z",
        stages={
            "bias_detection": _make_agent_result(
                "Bias Detector", "bias_detector",
                data={
                    "bias_score": 1,
                    "detected_biases": [],
                    "neutral_queries": ["What are the primary drivers of climate change?"],
                    "required_perspectives": ["climate science", "economics"],
                },
            ),
            "research": _make_agent_result(
                "Researcher", "researcher",
                content="Research findings here.",
                data={
                    "sources": [
                        {"title": "IPCC Report", "url": "https://ipcc.ch", "perspective": "scientific", "claims": ["CO2 is rising"]},
                    ],
                },
            ),
            "fact_checking": _make_agent_result(
                "Fact Checker", "fact_checker",
                data={
                    "verified_claims": [
                        {"claim": "CO2 levels rising", "status": "VERIFIED", "confidence": 0.98},
                    ],
                },
            ),
            "devils_advocate": _make_agent_result(
                "Devil's Advocate", "devils_advocate",
                content="Challenges raised.",
                data={
                    "challenges": [
                        {"challenge": "Natural cycles also matter", "severity": "medium", "type": "scope", "recommendation": "Include paleoclimate data"},
                    ],
                },
            ),
            "synthesis": _make_agent_result("Synthesizer", "synthesizer", content="The synthesized report."),
            "evaluation": _make_agent_result(
                "Evaluator", "evaluator",
                data={
                    "scores": {"accuracy": 0.9, "balance": 0.85, "overall_score": 0.88},
                    "grade": "A-",
                    "improvements": ["Add economic impact data"],
                },
            ),
        },
        final_report="The synthesized report.",
        evaluation_scores={"accuracy": 0.9, "balance": 0.85, "overall_score": 0.88},
        overall_grade="A-",
        total_tokens={"input": 600, "output": 300},
        duration_seconds=22.3,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReportGenerator:
    """Test ReportGenerator.generate()."""

    def test_generates_markdown_file(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        result = _make_pipeline_result()
        path = gen.generate(result)

        assert path.exists()
        assert path.suffix == ".md"
        assert path.stat().st_size > 0

    def test_report_contains_header(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "# C.L.E.R.I.C. Research Report" in content
        assert "What causes climate change?" in content
        assert "A-" in content

    def test_report_contains_bias_section(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 1. Bias Analysis" in content
        assert "1/10" in content

    def test_report_contains_research_section(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 2. Research Findings" in content
        assert "IPCC Report" in content

    def test_report_contains_factcheck_section(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 3. Fact Verification" in content
        assert "VERIFIED" in content

    def test_report_contains_challenges_section(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 4. Adversarial Challenges" in content
        assert "Natural cycles" in content

    def test_report_contains_synthesized_report(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 5. Synthesized Report" in content
        assert "The synthesized report." in content

    def test_report_contains_evaluation_section(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 6. Quality Evaluation" in content
        assert "A-" in content

    def test_report_contains_metadata_section(self, tmp_path: Path):
        gen = ReportGenerator(str(tmp_path / "reports"))
        path = gen.generate(_make_pipeline_result())
        content = path.read_text(encoding="utf-8")

        assert "## 7. Pipeline Metadata" in content
        assert "900" in content  # 600 + 300 total tokens
        assert "22.3" in content
