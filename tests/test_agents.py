"""Tests for cleric.agents.base.BaseAgent and BiasDetectorAgent."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cleric.agents.base import BaseAgent, AgentResult
from cleric.agents.bias_detector import BiasDetectorAgent
from cleric.config import Config
from cleric.tools.registry import ToolRegistry


class TestBaseAgentRun:
    """Test the agentic loop in BaseAgent.run()."""

    def _make_agent(self, config, tools=None):
        """Create a BaseAgent with a mocked Anthropic client."""
        agent = BaseAgent(
            name="Test Agent",
            role="tester",
            system_prompt="You are a test agent.",
            config=config,
            tools=tools,
        )
        agent.client = MagicMock()
        return agent

    def test_run_simple_text_response(self, mock_config, mock_anthropic_response):
        agent = self._make_agent(mock_config)
        response = mock_anthropic_response("text", content="The answer is 42.")
        agent.client.messages.create.return_value = response

        result = agent.run("What is the meaning of life?")

        assert isinstance(result, AgentResult)
        assert result.agent_name == "Test Agent"
        assert result.role == "tester"
        assert result.content == "The answer is 42."
        assert result.tool_calls_made == []
        assert result.tokens_used["input"] == 100
        assert result.tokens_used["output"] == 50

    def test_run_with_tool_use_loop(self, mock_config, mock_anthropic_response, tool_registry):
        """Agent calls a tool, gets result, then produces final text."""
        agent = self._make_agent(mock_config, tools=tool_registry)

        tool_response = mock_anthropic_response(
            "tool_use",
            tool_name="echo",
            tool_input={"text": "hello"},
            tool_id="toolu_abc",
        )
        final_response = mock_anthropic_response("text", content="Tool said: echo: hello")

        agent.client.messages.create.side_effect = [tool_response, final_response]

        result = agent.run("Echo hello for me.")

        assert result.content == "Tool said: echo: hello"
        assert len(result.tool_calls_made) == 1
        assert result.tool_calls_made[0]["tool"] == "echo"
        assert result.tokens_used["input"] == 200  # 100 + 100
        assert result.tokens_used["output"] == 100  # 50 + 50

    def test_run_with_context(self, mock_config, mock_anthropic_response):
        agent = self._make_agent(mock_config)
        response = mock_anthropic_response("text", content="Got context.")
        agent.client.messages.create.return_value = response

        result = agent.run("Do analysis.", context={"upstream": "Some prior output"})

        # Verify the message sent to the API contained the context
        call_kwargs = agent.client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 1
        assert "Context from other agents" in messages[0]["content"]
        assert "upstream" in messages[0]["content"]
        assert "Some prior output" in messages[0]["content"]

    def test_run_no_context(self, mock_config, mock_anthropic_response):
        agent = self._make_agent(mock_config)
        response = mock_anthropic_response("text", content="No context.")
        agent.client.messages.create.return_value = response

        agent.run("Plain prompt.")

        call_kwargs = agent.client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert messages[0]["content"] == "Plain prompt."


class TestParseStructuredData:
    """Test _parse_structured_data JSON extraction."""

    def _make_agent(self, config):
        agent = BaseAgent(
            name="Parser",
            role="parser",
            system_prompt="test",
            config=config,
        )
        return agent

    def test_extracts_json_block(self, mock_config):
        agent = self._make_agent(mock_config)
        text = 'Here is the analysis:\n\n```json\n{"bias_score": 3, "key": "value"}\n```\n\nDone.'
        data = agent._parse_structured_data(text)
        assert data["bias_score"] == 3
        assert data["key"] == "value"

    def test_merges_multiple_json_blocks(self, mock_config):
        agent = self._make_agent(mock_config)
        text = '```json\n{"a": 1}\n```\ntext\n```json\n{"b": 2}\n```'
        data = agent._parse_structured_data(text)
        assert data["a"] == 1
        assert data["b"] == 2

    def test_non_dict_json_stored_with_index_key(self, mock_config):
        agent = self._make_agent(mock_config)
        text = '```json\n[1, 2, 3]\n```'
        data = agent._parse_structured_data(text)
        assert data["data_0"] == [1, 2, 3]

    def test_no_json_blocks_returns_empty(self, mock_config):
        agent = self._make_agent(mock_config)
        data = agent._parse_structured_data("Just plain text, no JSON.")
        assert data == {}

    def test_invalid_json_is_skipped(self, mock_config):
        agent = self._make_agent(mock_config)
        text = '```json\n{invalid json\n```\n```json\n{"valid": true}\n```'
        data = agent._parse_structured_data(text)
        assert data == {"valid": True}


class TestBiasDetectorAgent:
    """Test BiasDetectorAgent construction and identity."""

    def test_has_correct_name_and_role(self, mock_config):
        agent = BiasDetectorAgent(mock_config)
        assert agent.name == "Bias Detector"
        assert agent.role == "bias_detector"

    def test_has_no_tools(self, mock_config):
        agent = BiasDetectorAgent(mock_config)
        assert agent.tools is None

    def test_system_prompt_is_set(self, mock_config):
        agent = BiasDetectorAgent(mock_config)
        assert "Bias Detector" in agent.system_prompt
        assert "submit_results" in agent.system_prompt

    def test_repr(self, mock_config):
        agent = BiasDetectorAgent(mock_config)
        r = repr(agent)
        assert "BiasDetectorAgent" in r
        assert "Bias Detector" in r
