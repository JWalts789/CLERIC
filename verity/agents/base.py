"""Base agent class that handles Claude API interaction with tool use.

Every Verity agent inherits from BaseAgent, which owns the agentic loop:
send a message, execute any tool calls Claude requests, feed results back,
and repeat until a final text response is produced.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from anthropic import Anthropic

from verity.config import Config
from verity.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Structured result from any agent run.

    Attributes:
        agent_name: Human-readable name of the agent that produced this result.
        role: Short label for the agent's function (e.g. "bias_detector").
        content: Full text output from the agent.
        data: Structured data extracted from JSON code blocks in the response.
        tool_calls_made: Chronological log of every tool invocation.
        tokens_used: Token consumption breakdown {"input": int, "output": int}.
    """

    agent_name: str
    role: str
    content: str
    data: dict = field(default_factory=dict)
    tool_calls_made: list[dict] = field(default_factory=list)
    tokens_used: dict = field(default_factory=dict)


class BaseAgent:
    """Abstract base for all Verity agents.

    Subclasses typically only need to supply a system prompt and optionally
    override ``_parse_structured_data`` for custom extraction logic.

    Args:
        name: Display name shown in logs and results.
        role: Short role identifier (e.g. "researcher", "fact_checker").
        system_prompt: The full system prompt that defines this agent's behavior.
        config: Application-wide configuration (model, tokens, API key).
        tools: Optional tool registry.  Agents that don't need tools pass None.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        config: Config,
        tools: ToolRegistry | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.config = config
        self.tools = tools
        self.client = Anthropic(api_key=config.anthropic_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, prompt: str, context: dict[str, str] | None = None) -> AgentResult:
        """Run this agent with the given prompt and optional upstream context.

        Implements the full tool-use agentic loop:

        1. Build the initial message (with optional context from prior agents).
        2. Call Claude.
        3. If Claude requests tool use, execute each tool and feed results back.
        4. Repeat until Claude produces a final text response.
        5. Parse any embedded JSON data blocks and return an ``AgentResult``.

        Args:
            prompt: The task or question for this agent.
            context: Key-value pairs of upstream agent outputs to prepend.

        Returns:
            An ``AgentResult`` containing the agent's full output and metadata.
        """
        messages = self._build_initial_messages(prompt, context)

        tool_calls_made: list[dict] = []
        total_input_tokens = 0
        total_output_tokens = 0

        while True:
            response = self._call_api(messages)

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            if response.stop_reason == "tool_use":
                self._handle_tool_use(response, messages, tool_calls_made)
            else:
                return self._build_result(
                    response,
                    tool_calls_made,
                    total_input_tokens,
                    total_output_tokens,
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_initial_messages(
        self, prompt: str, context: dict[str, str] | None
    ) -> list[dict]:
        """Construct the opening messages list, optionally prepending context."""
        if context:
            context_lines = "\n".join(
                f"**{key}**: {value}" for key, value in context.items()
            )
            prompt = (
                f"## Context from other agents:\n{context_lines}\n\n"
                f"## Your task:\n{prompt}"
            )
        return [{"role": "user", "content": prompt}]

    def _call_api(self, messages: list[dict]):
        """Send a single request to the Claude API."""
        kwargs: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools.get_schemas()

        logger.debug("%s calling Claude API (messages=%d)", self.name, len(messages))
        return self.client.messages.create(**kwargs)

    def _handle_tool_use(
        self,
        response,
        messages: list[dict],
        tool_calls_made: list[dict],
    ) -> None:
        """Execute every tool_use block in the response and append results."""
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results: list[dict] = []
        for block in assistant_content:
            if block.type != "tool_use":
                continue

            logger.info(
                "%s calling tool %s with %s",
                self.name,
                block.name,
                json.dumps(block.input, default=str)[:200],
            )

            result = self.tools.execute(block.name, block.input)

            tool_calls_made.append(
                {
                    "tool": block.name,
                    "input": block.input,
                    "result_preview": str(result)[:200],
                }
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    def _build_result(
        self,
        response,
        tool_calls_made: list[dict],
        total_input_tokens: int,
        total_output_tokens: int,
    ) -> AgentResult:
        """Extract text content and structured data from the final response."""
        text_parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        text_content = "".join(text_parts)
        data = self._parse_structured_data(text_content)

        logger.info(
            "%s finished (tokens: in=%d out=%d, tools=%d)",
            self.name,
            total_input_tokens,
            total_output_tokens,
            len(tool_calls_made),
        )

        return AgentResult(
            agent_name=self.name,
            role=self.role,
            content=text_content,
            data=data,
            tool_calls_made=tool_calls_made,
            tokens_used={"input": total_input_tokens, "output": total_output_tokens},
        )

    def _parse_structured_data(self, text: str) -> dict:
        """Extract JSON data blocks from agent response text.

        Agents are prompted to embed structured output inside fenced
        ``json`` code blocks.  This method finds all such blocks, parses
        them, and merges any top-level dicts into a single dict.

        Returns:
            Merged dictionary of all successfully parsed JSON blocks.
        """
        data: dict = {}
        json_blocks = re.findall(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        for idx, block in enumerate(json_blocks):
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict):
                    data.update(parsed)
                else:
                    data[f"data_{idx}"] = parsed
            except json.JSONDecodeError:
                logger.warning(
                    "%s produced invalid JSON block #%d", self.name, idx
                )
        return data

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} role={self.role!r}>"
