"""Tests for cleric.cli — the command-line interface."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cleric.agents.base import AgentResult
from cleric.orchestrator import PipelineResult


class TestCLINoArgs:
    """When invoked with no query, the CLI should show the help panel and exit."""

    def test_no_args_shows_help_and_exits(self):
        with patch("sys.argv", ["cleric"]):
            with pytest.raises(SystemExit) as exc_info:
                from cleric.cli import main
                main()
            assert exc_info.value.code == 0


class TestCLIWithQuery:
    """When invoked with a query, the CLI should run the pipeline."""

    def _make_fake_result(self):
        """Build a minimal PipelineResult for testing."""
        bias_result = AgentResult(
            agent_name="Bias Detector",
            role="bias_detector",
            content="Bias analysis done.",
            data={"bias_score": 2, "neutral_queries": ["neutral query 1"]},
            tool_calls_made=[],
            tokens_used={"input": 50, "output": 25},
        )
        eval_result = AgentResult(
            agent_name="Evaluator",
            role="evaluator",
            content="Evaluation done.",
            data={
                "scores": {"accuracy": 0.9, "balance": 0.8},
                "grade": "A",
            },
            tool_calls_made=[],
            tokens_used={"input": 50, "output": 25},
        )
        return PipelineResult(
            query="test query",
            timestamp="2026-01-01T00:00:00Z",
            stages={
                "bias_detection": bias_result,
                "evaluation": eval_result,
            },
            final_report="# Test Report\n\nThis is a test.",
            evaluation_scores={"accuracy": 0.9},
            overall_grade="A",
            total_tokens={"input": 100, "output": 50},
            duration_seconds=1.5,
        )

    def _make_mock_config(self, tmp_dir):
        """Create a mock config with a real temporary output_dir."""
        mock_config = MagicMock()
        mock_config.output_dir = str(tmp_dir)
        mock_config.model = "claude-sonnet-4-6"
        return mock_config

    @patch("cleric.cli.MermaidGenerator")
    @patch("cleric.cli.ReportGenerator")
    @patch("cleric.cli.ResearchPipeline")
    @patch("cleric.cli.Config")
    def test_query_runs_pipeline(self, MockConfig, MockPipeline, MockReport, MockMermaid, tmp_path):
        fake_result = self._make_fake_result()
        mock_pipeline_inst = MagicMock()
        mock_pipeline_inst.run.return_value = fake_result
        MockPipeline.return_value = mock_pipeline_inst
        MockConfig.from_env.return_value = self._make_mock_config(tmp_path)

        mock_mermaid_inst = MagicMock()
        mock_mermaid_inst.generate_all.return_value = {"flow": str(tmp_path / "test_flow.mmd")}
        MockMermaid.return_value = mock_mermaid_inst

        mock_report_inst = MagicMock()
        mock_report_inst.generate.return_value = str(tmp_path / "report.md")
        MockReport.return_value = mock_report_inst

        with patch("sys.argv", ["cleric", "test query"]):
            from cleric.cli import main
            main()

        mock_pipeline_inst.run.assert_called_once_with("test query")

    @patch("cleric.cli.ResearchPipeline")
    @patch("cleric.cli.Config")
    def test_json_flag_outputs_json(self, MockConfig, MockPipeline, tmp_path):
        fake_result = self._make_fake_result()
        mock_pipeline_inst = MagicMock()
        mock_pipeline_inst.run.return_value = fake_result
        MockPipeline.return_value = mock_pipeline_inst
        MockConfig.from_env.return_value = self._make_mock_config(tmp_path)

        with patch("sys.argv", ["cleric", "--json", "test query"]):
            from cleric.cli import main
            main()

        mock_pipeline_inst.run.assert_called_once_with("test query")

    @patch("cleric.cli.MermaidGenerator")
    @patch("cleric.cli.ReportGenerator")
    @patch("cleric.cli.ResearchPipeline")
    @patch("cleric.cli.Config")
    def test_model_override(self, MockConfig, MockPipeline, MockReport, MockMermaid, tmp_path):
        fake_result = self._make_fake_result()
        mock_pipeline_inst = MagicMock()
        mock_pipeline_inst.run.return_value = fake_result
        MockPipeline.return_value = mock_pipeline_inst
        mock_config = self._make_mock_config(tmp_path)
        MockConfig.from_env.return_value = mock_config

        mock_mermaid_inst = MagicMock()
        mock_mermaid_inst.generate_all.return_value = {"flow": str(tmp_path / "test_flow.mmd")}
        MockMermaid.return_value = mock_mermaid_inst
        mock_report_inst = MagicMock()
        mock_report_inst.generate.return_value = str(tmp_path / "report.md")
        MockReport.return_value = mock_report_inst

        with patch("sys.argv", ["cleric", "--model", "claude-opus-4-6", "test query"]):
            from cleric.cli import main
            main()

        assert mock_config.model == "claude-opus-4-6"

    @patch("cleric.cli.MermaidGenerator")
    @patch("cleric.cli.ReportGenerator")
    @patch("cleric.cli.ResearchPipeline")
    @patch("cleric.cli.Config")
    def test_verbose_flag(self, MockConfig, MockPipeline, MockReport, MockMermaid, tmp_path):
        fake_result = self._make_fake_result()
        mock_pipeline_inst = MagicMock()
        mock_pipeline_inst.run.return_value = fake_result
        MockPipeline.return_value = mock_pipeline_inst
        MockConfig.from_env.return_value = self._make_mock_config(tmp_path)

        mock_mermaid_inst = MagicMock()
        mock_mermaid_inst.generate_all.return_value = {"flow": str(tmp_path / "test_flow.mmd")}
        MockMermaid.return_value = mock_mermaid_inst
        mock_report_inst = MagicMock()
        mock_report_inst.generate.return_value = str(tmp_path / "report.md")
        MockReport.return_value = mock_report_inst

        with patch("sys.argv", ["cleric", "--verbose", "test query"]):
            from cleric.cli import main
            main()

        mock_pipeline_inst.run.assert_called_once()

    @patch("cleric.cli.ResearchPipeline")
    @patch("cleric.cli.Config")
    def test_no_mermaid_no_report_flags(self, MockConfig, MockPipeline, tmp_path):
        fake_result = self._make_fake_result()
        mock_pipeline_inst = MagicMock()
        mock_pipeline_inst.run.return_value = fake_result
        MockPipeline.return_value = mock_pipeline_inst
        MockConfig.from_env.return_value = self._make_mock_config(tmp_path)

        with patch("sys.argv", ["cleric", "--json", "--no-mermaid", "--no-report", "test query"]):
            from cleric.cli import main
            main()

        mock_pipeline_inst.run.assert_called_once()

    @patch("cleric.cli.ResearchPipeline")
    @patch("cleric.cli.Config")
    def test_output_dir_override(self, MockConfig, MockPipeline, tmp_path):
        fake_result = self._make_fake_result()
        mock_pipeline_inst = MagicMock()
        mock_pipeline_inst.run.return_value = fake_result
        MockPipeline.return_value = mock_pipeline_inst
        mock_config = self._make_mock_config(tmp_path)
        MockConfig.from_env.return_value = mock_config

        custom_dir = str(tmp_path / "custom_output")
        with patch("sys.argv", ["cleric", "--json", "--output-dir", custom_dir, "test query"]):
            from cleric.cli import main
            main()

        assert mock_config.output_dir == custom_dir


class TestDisplayResults:
    """Test the _display_results helper function."""

    def test_display_results_no_crash(self):
        """_display_results should not crash with valid data."""
        from cleric.cli import _display_results

        bias_result = AgentResult(
            agent_name="Bias Detector",
            role="bias_detector",
            content="Analysis.",
            data={"bias_score": 7, "neutral_queries": ["q1"]},
            tokens_used={"input": 10, "output": 5},
        )
        eval_result = AgentResult(
            agent_name="Evaluator",
            role="evaluator",
            content="Evaluation.",
            data={
                "scores": {"accuracy": 0.5, "balance": 0.3},
                "grade": "C",
            },
            tokens_used={"input": 10, "output": 5},
        )
        result = PipelineResult(
            query="test",
            timestamp="2026-01-01",
            stages={"bias_detection": bias_result, "evaluation": eval_result},
            final_report="Report text",
            total_tokens={"input": 20, "output": 10},
            duration_seconds=1.0,
        )
        # Should not raise
        _display_results(result, verbose=True)

    def test_display_results_empty_stages(self):
        """_display_results should handle missing stages gracefully."""
        from cleric.cli import _display_results

        result = PipelineResult(
            query="test",
            timestamp="2026-01-01",
            stages={},
            final_report="",
            total_tokens={"input": 0, "output": 0},
            duration_seconds=0.0,
        )
        _display_results(result, verbose=False)

    def test_display_results_low_bias_score(self):
        """Green color path: bias_score <= 3."""
        from cleric.cli import _display_results

        bias_result = AgentResult(
            agent_name="Bias Detector",
            role="bias_detector",
            content="Low bias.",
            data={"bias_score": 1, "neutral_queries": ["q"]},
            tokens_used={"input": 5, "output": 5},
        )
        result = PipelineResult(
            query="test",
            timestamp="2026-01-01",
            stages={"bias_detection": bias_result},
            final_report="Report",
            total_tokens={"input": 5, "output": 5},
            duration_seconds=0.5,
        )
        _display_results(result, verbose=False)

    def test_display_results_non_numeric_score(self):
        """Non-numeric scores in evaluation should not crash."""
        from cleric.cli import _display_results

        eval_result = AgentResult(
            agent_name="Evaluator",
            role="evaluator",
            content="Eval.",
            data={
                "scores": {"accuracy": "high", "balance": 0.7},
                "grade": "B",
            },
            tokens_used={"input": 5, "output": 5},
        )
        result = PipelineResult(
            query="test",
            timestamp="2026-01-01",
            stages={"evaluation": eval_result},
            final_report="Report",
            total_tokens={"input": 5, "output": 5},
            duration_seconds=0.5,
        )
        _display_results(result, verbose=False)


class TestMainModule:
    """Test __main__.py entry point."""

    def test_main_module_importable(self):
        """python -m cleric module should be importable."""
        # We can't easily re-execute __main__ without it calling main(),
        # but we can verify the module structure
        with patch("cleric.cli.main"):
            import importlib
            import cleric.__main__
            importlib.reload(cleric.__main__)
