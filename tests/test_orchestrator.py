"""Tests for verity.orchestrator — PipelineResult and ResearchPipeline."""

from unittest.mock import MagicMock, patch

import pytest

from verity.agents.base import AgentResult
from verity.orchestrator import PipelineResult, ResearchPipeline
from verity.config import Config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_result(name: str, role: str, content: str = "output", data: dict | None = None) -> AgentResult:
    return AgentResult(
        agent_name=name,
        role=role,
        content=content,
        data=data or {},
        tool_calls_made=[],
        tokens_used={"input": 50, "output": 30},
    )


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------

class TestPipelineResult:
    """Test PipelineResult serialization."""

    def test_to_dict_basic(self):
        result = PipelineResult(
            query="Is the sky blue?",
            timestamp="2026-01-01T00:00:00Z",
            duration_seconds=12.5,
            overall_grade="A",
            total_tokens={"input": 500, "output": 300},
        )
        d = result.to_dict()
        assert d["query"] == "Is the sky blue?"
        assert d["timestamp"] == "2026-01-01T00:00:00Z"
        assert d["duration_seconds"] == 12.5
        assert d["overall_grade"] == "A"
        assert d["total_tokens"] == {"input": 500, "output": 300}
        assert d["stages"] == {}

    def test_to_dict_with_stages(self):
        ar = _make_agent_result("Bias Detector", "bias_detector", data={"bias_score": 2})
        result = PipelineResult(
            query="test",
            timestamp="2026-01-01T00:00:00Z",
            stages={"bias_detection": ar},
        )
        d = result.to_dict()
        assert "bias_detection" in d["stages"]
        stage = d["stages"]["bias_detection"]
        assert stage["agent"] == "Bias Detector"
        assert stage["role"] == "bias_detector"
        assert stage["data"]["bias_score"] == 2

    def test_to_dict_evaluation_and_grade(self):
        result = PipelineResult(
            query="test",
            timestamp="now",
            evaluation_scores={"accuracy": 0.9, "overall_score": 0.85},
            overall_grade="B+",
        )
        d = result.to_dict()
        assert d["evaluation"]["accuracy"] == 0.9
        assert d["overall_grade"] == "B+"


# ---------------------------------------------------------------------------
# ResearchPipeline
# ---------------------------------------------------------------------------

class TestResearchPipeline:
    """Test the pipeline orchestration with all agents mocked."""

    def _mock_agent_class(self, name: str, role: str, data: dict | None = None):
        """Return a mock agent class whose instances have a .run() returning an AgentResult."""
        agent_instance = MagicMock()
        agent_instance.run.return_value = _make_agent_result(name, role, data=data or {})
        mock_cls = MagicMock(return_value=agent_instance)
        return mock_cls

    @patch("verity.orchestrator.EvaluatorAgent")
    @patch("verity.orchestrator.SynthesizerAgent")
    @patch("verity.orchestrator.DevilsAdvocateAgent")
    @patch("verity.orchestrator.FactCheckerAgent")
    @patch("verity.orchestrator.ResearcherAgent")
    @patch("verity.orchestrator.BiasDetectorAgent")
    @patch("verity.orchestrator.create_default_registry")
    def test_pipeline_runs_all_stages(
        self,
        mock_registry,
        MockBias,
        MockResearcher,
        MockFactChecker,
        MockDevil,
        MockSynthesizer,
        MockEvaluator,
        mock_config,
    ):
        mock_registry.return_value = MagicMock()

        # Set up each mock agent
        bias_data = {"bias_score": 2, "neutral_queries": ["neutral q"], "required_perspectives": ["academic"]}
        MockBias.return_value.run.return_value = _make_agent_result("Bias Detector", "bias_detector", data=bias_data)
        MockResearcher.return_value.run.return_value = _make_agent_result("Researcher", "researcher", data={"sources": []})
        MockFactChecker.return_value.run.return_value = _make_agent_result("Fact Checker", "fact_checker", data={"claims": []})
        MockDevil.return_value.run.return_value = _make_agent_result("Devil's Advocate", "devils_advocate")
        MockSynthesizer.return_value.run.return_value = _make_agent_result("Synthesizer", "synthesizer", content="Final report text.")
        MockEvaluator.return_value.run.return_value = _make_agent_result(
            "Evaluator", "evaluator",
            data={"scores": {"overall_score": 0.85}, "grade": "B+"},
        )

        pipeline = ResearchPipeline(config=mock_config)
        result = pipeline.run("Is the sky blue?")

        assert isinstance(result, PipelineResult)
        assert result.query == "Is the sky blue?"
        assert "bias_detection" in result.stages
        assert "research" in result.stages
        assert "fact_checking" in result.stages
        assert "devils_advocate" in result.stages
        assert "synthesis" in result.stages
        assert "evaluation" in result.stages
        assert result.final_report == "Final report text."
        assert result.overall_grade == "B+"
        assert result.evaluation_scores == {"overall_score": 0.85}
        assert result.duration_seconds >= 0

    @patch("verity.orchestrator.EvaluatorAgent")
    @patch("verity.orchestrator.SynthesizerAgent")
    @patch("verity.orchestrator.DevilsAdvocateAgent")
    @patch("verity.orchestrator.FactCheckerAgent")
    @patch("verity.orchestrator.ResearcherAgent")
    @patch("verity.orchestrator.BiasDetectorAgent")
    @patch("verity.orchestrator.create_default_registry")
    def test_callbacks_fire_in_order(
        self,
        mock_registry,
        MockBias,
        MockResearcher,
        MockFactChecker,
        MockDevil,
        MockSynthesizer,
        MockEvaluator,
        mock_config,
    ):
        mock_registry.return_value = MagicMock()

        for mock_cls in [MockBias, MockResearcher, MockFactChecker, MockDevil, MockSynthesizer]:
            mock_cls.return_value.run.return_value = _make_agent_result("A", "a")
        MockEvaluator.return_value.run.return_value = _make_agent_result(
            "Evaluator", "evaluator", data={"scores": {"overall_score": 0.5}, "grade": "C"}
        )

        pipeline = ResearchPipeline(config=mock_config)

        started = []
        completed = []
        pipeline.on_stage_start(lambda stage: started.append(stage))
        pipeline.on_stage_complete(lambda stage, _result: completed.append(stage))

        pipeline.run("test query")

        expected_stages = [
            "bias_detection", "research", "fact_checking",
            "devils_advocate", "synthesis", "evaluation",
        ]
        assert started == expected_stages
        assert completed == expected_stages

    @patch("verity.orchestrator.EvaluatorAgent")
    @patch("verity.orchestrator.SynthesizerAgent")
    @patch("verity.orchestrator.DevilsAdvocateAgent")
    @patch("verity.orchestrator.FactCheckerAgent")
    @patch("verity.orchestrator.ResearcherAgent")
    @patch("verity.orchestrator.BiasDetectorAgent")
    @patch("verity.orchestrator.create_default_registry")
    def test_memory_storage_after_pipeline(
        self,
        mock_registry,
        MockBias,
        MockResearcher,
        MockFactChecker,
        MockDevil,
        MockSynthesizer,
        MockEvaluator,
        mock_config,
    ):
        mock_registry.return_value = MagicMock()

        for mock_cls in [MockBias, MockResearcher, MockFactChecker, MockDevil, MockSynthesizer]:
            mock_cls.return_value.run.return_value = _make_agent_result("A", "a")
        MockEvaluator.return_value.run.return_value = _make_agent_result(
            "Evaluator", "evaluator", data={"scores": {"overall_score": 0.7}, "grade": "B"}
        )

        pipeline = ResearchPipeline(config=mock_config)
        pipeline.run("Test memory storage")

        # Verify something was stored in memory
        entries = pipeline.memory.retrieve("Test memory storage")
        assert len(entries) >= 1
        assert entries[0].key == "evaluation"

    @patch("verity.orchestrator.EvaluatorAgent")
    @patch("verity.orchestrator.SynthesizerAgent")
    @patch("verity.orchestrator.DevilsAdvocateAgent")
    @patch("verity.orchestrator.FactCheckerAgent")
    @patch("verity.orchestrator.ResearcherAgent")
    @patch("verity.orchestrator.BiasDetectorAgent")
    @patch("verity.orchestrator.create_default_registry")
    def test_token_tallying(
        self,
        mock_registry,
        MockBias,
        MockResearcher,
        MockFactChecker,
        MockDevil,
        MockSynthesizer,
        MockEvaluator,
        mock_config,
    ):
        mock_registry.return_value = MagicMock()

        # Each agent returns 50 input + 30 output
        for mock_cls in [MockBias, MockResearcher, MockFactChecker, MockDevil, MockSynthesizer]:
            mock_cls.return_value.run.return_value = _make_agent_result("A", "a")
        MockEvaluator.return_value.run.return_value = _make_agent_result(
            "E", "evaluator", data={"scores": {"overall_score": 0.5}, "grade": "C"}
        )

        pipeline = ResearchPipeline(config=mock_config)
        result = pipeline.run("test")

        # 6 stages x 50 input = 300, 6 stages x 30 output = 180
        assert result.total_tokens["input"] == 300
        assert result.total_tokens["output"] == 180
