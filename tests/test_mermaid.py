"""Tests for cleric.output.mermaid.MermaidGenerator."""

from pathlib import Path

import pytest

from cleric.agents.base import AgentResult
from cleric.orchestrator import PipelineResult
from cleric.output.mermaid import MermaidGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_result(name: str, role: str, content: str = "", data: dict | None = None) -> AgentResult:
    return AgentResult(
        agent_name=name,
        role=role,
        content=content,
        data=data or {},
        tool_calls_made=[],
        tokens_used={"input": 100, "output": 50},
    )


def _make_pipeline_result(query: str = "Is the sky blue?") -> PipelineResult:
    """Build a minimal PipelineResult with all stages populated."""
    return PipelineResult(
        query=query,
        timestamp="2026-01-01T00:00:00Z",
        stages={
            "bias_detection": _make_agent_result(
                "Bias Detector", "bias_detector",
                data={
                    "bias_score": 3,
                    "detected_biases": [{"type": "loaded language", "quote": "obviously", "explanation": "presupposes"}],
                    "neutral_queries": ["What color is the sky?"],
                    "required_perspectives": ["atmospheric science", "philosophy"],
                },
            ),
            "research": _make_agent_result(
                "Researcher", "researcher",
                data={
                    "sources": [
                        {"title": "Sky Science", "url": "https://example.com/sky", "perspective": "scientific"},
                        {"title": "Color Theory", "url": "https://example.com/color", "perspective": "artistic"},
                    ],
                },
            ),
            "fact_checking": _make_agent_result(
                "Fact Checker", "fact_checker",
                data={
                    "verified_claims": [
                        {"claim": "Sky appears blue due to Rayleigh scattering", "status": "VERIFIED", "confidence": 0.95},
                        {"claim": "Sky is always blue", "status": "DISPUTED", "confidence": 0.3},
                    ],
                },
            ),
            "devils_advocate": _make_agent_result("Devil's Advocate", "devils_advocate"),
            "synthesis": _make_agent_result("Synthesizer", "synthesizer", content="Final report."),
            "evaluation": _make_agent_result(
                "Evaluator", "evaluator",
                data={
                    "scores": {"accuracy": 0.9, "balance": 0.8, "overall_score": 0.85},
                    "grade": "B+",
                    "improvements": ["Add more international sources"],
                },
            ),
        },
        final_report="Final report.",
        evaluation_scores={"accuracy": 0.9, "balance": 0.8, "overall_score": 0.85},
        overall_grade="B+",
        total_tokens={"input": 600, "output": 300},
        duration_seconds=15.2,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMermaidGenerator:
    """Test MermaidGenerator.generate_all and individual diagram methods."""

    def test_generate_all_produces_six_files(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        assert len(files) == 6
        expected_keys = {
            "pipeline_flow", "bias_analysis", "source_map",
            "verification_status", "evaluation_scorecard", "agent_interaction",
        }
        assert set(files.keys()) == expected_keys

        for name, path in files.items():
            assert path.exists(), f"{name} file was not created"
            assert path.suffix == ".mermaid"
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_pipeline_flow_contains_expected_content(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        content = files["pipeline_flow"].read_text(encoding="utf-8")
        assert "flowchart TD" in content
        assert "Bias Detector" in content
        assert "Researcher" in content
        assert "Fact Checker" in content
        assert "Synthesizer" in content
        assert "Evaluator" in content

    def test_bias_analysis_contains_score(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        content = files["bias_analysis"].read_text(encoding="utf-8")
        assert "3/10" in content
        assert "flowchart TD" in content

    def test_source_map_contains_sources(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        content = files["source_map"].read_text(encoding="utf-8")
        assert "Sky Science" in content
        assert "Color Theory" in content

    def test_verification_status_shows_claims(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        content = files["verification_status"].read_text(encoding="utf-8")
        assert "Rayleigh scattering" in content
        assert "VERIFIED" in content or "Verified" in content.title()

    def test_evaluation_scorecard_shows_grade(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        content = files["evaluation_scorecard"].read_text(encoding="utf-8")
        assert "B+" in content

    def test_agent_interaction_is_sequence_diagram(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path / "diagrams"))
        result = _make_pipeline_result()
        files = gen.generate_all(result)

        content = files["agent_interaction"].read_text(encoding="utf-8")
        assert "sequenceDiagram" in content


class TestMermaidEscape:
    """Test the _escape helper."""

    def test_escapes_quotes(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        assert gen._escape('He said "hello"') == "He said 'hello'"

    def test_escapes_angle_brackets(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        escaped = gen._escape("<tag>")
        # The implementation replaces & before < and >, so &lt; becomes &amp;lt;
        # The key point: raw < and > must not appear in output
        assert "<" not in escaped.replace("&lt;", "").replace("&gt;", "")
        assert "tag" in escaped

    def test_escapes_ampersand(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        assert "&amp;" in gen._escape("A & B")

    def test_escapes_newlines(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        assert "\n" not in gen._escape("line1\nline2")


class TestMermaidSlugify:
    """Test the _slugify helper."""

    def test_basic_slugify(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        assert gen._slugify("Is the sky blue?") == "is_the_sky_blue"

    def test_slugify_truncates_long_text(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        slug = gen._slugify("a" * 100)
        assert len(slug) <= 50

    def test_slugify_strips_special_chars(self, tmp_path: Path):
        gen = MermaidGenerator(str(tmp_path))
        slug = gen._slugify("Hello, World! @#$%")
        assert all(c.isalnum() or c == "_" for c in slug)
