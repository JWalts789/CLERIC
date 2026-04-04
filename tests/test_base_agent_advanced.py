"""Advanced tests for cleric.agents.base — parsing, cleaning, tool loop."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cleric.agents.base import BaseAgent, AgentResult
from cleric.config import Config
from cleric.tools.registry import ToolRegistry


class TestParseStructuredDataAdvanced:
    """Test advanced JSON extraction strategies in _parse_structured_data."""

    def _make_agent(self, config):
        agent = BaseAgent(
            name="Parser",
            role="parser",
            system_prompt="test",
            config=config,
        )
        return agent

    def test_bare_json_no_fences(self, mock_config):
        """Strategy 3: bare JSON object at the end of the response."""
        agent = self._make_agent(mock_config)
        text = "Here is my analysis.\n\n{\"score\": 42, \"label\": \"good\"}"
        data = agent._parse_structured_data(text)
        assert data["score"] == 42
        assert data["label"] == "good"

    def test_generic_fenced_block_without_json_tag(self, mock_config):
        """Strategy 2: fenced ``` block that contains JSON but no language tag."""
        agent = self._make_agent(mock_config)
        text = "Analysis:\n\n```\n{\"key\": \"value\", \"num\": 7}\n```\n\nDone."
        data = agent._parse_structured_data(text)
        assert data["key"] == "value"
        assert data["num"] == 7

    def test_generic_fenced_block_non_json_skipped(self, mock_config):
        """Generic fenced block that doesn't start with { should be ignored."""
        agent = self._make_agent(mock_config)
        text = "Code:\n\n```\nprint('hello')\n```\n\nDone."
        data = agent._parse_structured_data(text)
        assert data == {}

    def test_bare_json_multiline(self, mock_config):
        """Bare JSON spanning multiple lines at end of response."""
        agent = self._make_agent(mock_config)
        text = 'Analysis complete.\n{\n  "a": 1,\n  "b": 2\n}'
        data = agent._parse_structured_data(text)
        assert data["a"] == 1
        assert data["b"] == 2


class TestCleanJson:
    """Test _clean_json fixes common LLM JSON issues."""

    def test_removes_trailing_commas_before_brace(self):
        text = '{"a": 1, "b": 2,}'
        result = BaseAgent._clean_json(text)
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    def test_removes_trailing_commas_before_bracket(self):
        text = '[1, 2, 3,]'
        result = BaseAgent._clean_json(text)
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_removes_line_comments(self):
        text = '{\n  "key": "value", // this is a comment\n  "num": 42\n}'
        result = BaseAgent._clean_json(text)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["num"] == 42

    def test_removes_both_commas_and_comments(self):
        text = '{\n  "a": 1, // comment\n  "b": 2,\n}'
        result = BaseAgent._clean_json(text)
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    def test_clean_json_with_valid_json_unchanged(self):
        text = '{"valid": true}'
        result = BaseAgent._clean_json(text)
        assert json.loads(result) == {"valid": True}


class TestToolUseLoopMultipleCalls:
    """Test the agentic loop with multiple tool calls before final response."""

    def _make_agent(self, config, tools):
        agent = BaseAgent(
            name="Multi-tool Agent",
            role="tester",
            system_prompt="test",
            config=config,
            tools=tools,
        )
        agent.client = MagicMock()
        return agent

    def test_multiple_tool_calls_then_final(self, mock_config, mock_anthropic_response, tool_registry):
        """Agent makes two tool calls in sequence, then returns final text."""
        agent = self._make_agent(mock_config, tool_registry)

        # First response: tool call to echo
        tool_resp_1 = mock_anthropic_response(
            "tool_use", tool_name="echo", tool_input={"text": "first"}, tool_id="t1"
        )
        # Second response: another tool call to add
        tool_resp_2 = mock_anthropic_response(
            "tool_use", tool_name="add", tool_input={"a": 1, "b": 2}, tool_id="t2"
        )
        # Final response: text
        final_resp = mock_anthropic_response("text", content="Done with both tools.")

        agent.client.messages.create.side_effect = [tool_resp_1, tool_resp_2, final_resp]

        result = agent.run("Use both tools.")

        assert result.content == "Done with both tools."
        assert len(result.tool_calls_made) == 2
        assert result.tool_calls_made[0]["tool"] == "echo"
        assert result.tool_calls_made[1]["tool"] == "add"
        assert result.tokens_used["input"] == 300  # 100 * 3
        assert result.tokens_used["output"] == 150  # 50 * 3


class TestContextBuilding:
    """Test _build_initial_messages with context."""

    def _make_agent(self, config):
        agent = BaseAgent(
            name="Ctx Agent",
            role="ctx",
            system_prompt="test",
            config=config,
        )
        return agent

    def test_multiple_context_entries(self, mock_config):
        agent = self._make_agent(mock_config)
        context = {
            "Researcher": "Found evidence A and B.",
            "Fact Checker": "Confirmed A, disputed B.",
            "Devil's Advocate": "What about C?",
        }
        messages = agent._build_initial_messages("Synthesize.", context)
        content = messages[0]["content"]

        assert "Context from other agents" in content
        assert "Researcher" in content
        assert "Found evidence A and B." in content
        assert "Fact Checker" in content
        assert "Devil's Advocate" in content
        assert "Your task" in content
        assert "Synthesize." in content

    def test_no_context_plain_prompt(self, mock_config):
        agent = self._make_agent(mock_config)
        messages = agent._build_initial_messages("Just do it.", None)
        assert messages[0]["content"] == "Just do it."


class TestSubmitResultsTool:
    """Test the submit_results virtual tool for structured output."""

    def _make_agent_with_schema(self, config, schema, tools=None):
        agent = BaseAgent(
            name="Schema Agent",
            role="schema_tester",
            system_prompt="test",
            config=config,
            tools=tools,
        )
        agent.output_schema = schema
        agent.client = MagicMock()
        return agent

    def test_submit_results_captures_data(self, mock_config, mock_anthropic_response):
        """When Claude calls submit_results, the data is captured in the result."""
        schema = {
            "type": "object",
            "properties": {"score": {"type": "integer"}},
            "required": ["score"],
        }
        agent = self._make_agent_with_schema(mock_config, schema)

        # First response: Claude calls submit_results
        tool_response = mock_anthropic_response(
            "tool_use",
            tool_name="submit_results",
            tool_input={"score": 7},
            tool_id="toolu_sr1",
        )
        # Second response: final text after tool result
        final_response = mock_anthropic_response("text", content="Analysis complete.")

        agent.client.messages.create.side_effect = [tool_response, final_response]

        result = agent.run("Score this.")
        assert result.data == {"score": 7}
        assert result.content == "Analysis complete."
        assert len(result.tool_calls_made) == 1
        assert result.tool_calls_made[0]["tool"] == "submit_results"

    def test_submit_results_tool_included_in_api_call(self, mock_config, mock_anthropic_response):
        """The submit_results tool schema is sent to the API when output_schema is set."""
        schema = {
            "type": "object",
            "properties": {"grade": {"type": "string"}},
            "required": ["grade"],
        }
        agent = self._make_agent_with_schema(mock_config, schema)

        response = mock_anthropic_response("text", content="Done.")
        agent.client.messages.create.return_value = response

        agent.run("Grade this.")

        call_kwargs = agent.client.messages.create.call_args.kwargs
        tools = call_kwargs["tools"]
        tool_names = [t["name"] for t in tools]
        assert "submit_results" in tool_names

    def test_submit_results_with_real_tools(self, mock_config, mock_anthropic_response, tool_registry):
        """submit_results works alongside real tools (echo, add)."""
        schema = {
            "type": "object",
            "properties": {"result": {"type": "string"}},
            "required": ["result"],
        }
        agent = self._make_agent_with_schema(mock_config, schema, tools=tool_registry)

        # Step 1: Claude calls a real tool (echo)
        tool_resp = mock_anthropic_response(
            "tool_use", tool_name="echo", tool_input={"text": "hello"}, tool_id="t1"
        )
        # Step 2: Claude calls submit_results
        sr_resp = mock_anthropic_response(
            "tool_use",
            tool_name="submit_results",
            tool_input={"result": "echo said hello"},
            tool_id="t2",
        )
        # Step 3: final text
        final_resp = mock_anthropic_response("text", content="All done.")

        agent.client.messages.create.side_effect = [tool_resp, sr_resp, final_resp]

        result = agent.run("Echo then submit.")
        assert result.data == {"result": "echo said hello"}
        assert len(result.tool_calls_made) == 2
        assert result.tool_calls_made[0]["tool"] == "echo"
        assert result.tool_calls_made[1]["tool"] == "submit_results"

    def test_fallback_to_json_parsing_when_no_schema(self, mock_config, mock_anthropic_response):
        """When output_schema is None, JSON block parsing still works."""
        agent = BaseAgent(
            name="No Schema",
            role="fallback",
            system_prompt="test",
            config=mock_config,
        )
        agent.client = MagicMock()

        response = mock_anthropic_response(
            "text",
            content='Analysis.\n```json\n{"score": 8}\n```',
        )
        agent.client.messages.create.return_value = response

        result = agent.run("Analyze.")
        assert result.data["score"] == 8

    def test_fallback_to_json_parsing_when_submit_not_called(self, mock_config, mock_anthropic_response):
        """If model has output_schema but never calls submit_results, JSON parsing kicks in."""
        schema = {
            "type": "object",
            "properties": {"score": {"type": "integer"}},
            "required": ["score"],
        }
        agent = self._make_agent_with_schema(mock_config, schema)

        # Model returns text with JSON block but never calls submit_results
        response = mock_anthropic_response(
            "text",
            content='Here is my score.\n```json\n{"score": 5}\n```',
        )
        agent.client.messages.create.return_value = response

        result = agent.run("Score this.")
        assert result.data["score"] == 5

    def test_no_tools_kwarg_when_no_schema_and_no_tools(self, mock_config, mock_anthropic_response):
        """When there's no output_schema and no tools, tools kwarg is not sent."""
        agent = BaseAgent(
            name="Plain",
            role="plain",
            system_prompt="test",
            config=mock_config,
        )
        agent.client = MagicMock()

        response = mock_anthropic_response("text", content="Done.")
        agent.client.messages.create.return_value = response

        agent.run("Hi.")

        call_kwargs = agent.client.messages.create.call_args.kwargs
        assert "tools" not in call_kwargs


class TestAgentRepr:
    """Test BaseAgent __repr__."""

    def test_repr_format(self, mock_config):
        agent = BaseAgent(
            name="Test Agent",
            role="tester",
            system_prompt="test",
            config=mock_config,
        )
        r = repr(agent)
        assert "BaseAgent" in r
        assert "Test Agent" in r
        assert "tester" in r
