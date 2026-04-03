"""Shared fixtures for the Verity test suite.

All tests run WITHOUT an API key — the Anthropic client is always mocked.
"""

import os
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from verity.config import Config
from verity.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_config(tmp_path: Path) -> Config:
    """Config with a fake API key and temp directories."""
    return Config(
        anthropic_api_key="fake-key-for-testing",
        model="claude-sonnet-4-6",
        max_search_results=5,
        memory_dir=tmp_path / "memory",
        output_dir=tmp_path / "output",
        max_tokens=1024,
    )


# ---------------------------------------------------------------------------
# Anthropic API response helpers
# ---------------------------------------------------------------------------

def _make_text_block(text: str):
    """Create a mock text content block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(tool_name: str, tool_input: dict, tool_id: str = "toolu_001"):
    """Create a mock tool_use content block."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = tool_id
    return block


def _make_usage(input_tokens: int = 100, output_tokens: int = 50):
    """Create a mock usage object."""
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    return usage


@pytest.fixture
def mock_anthropic_response():
    """Factory that builds mock Claude API responses.

    Usage:
        response = mock_anthropic_response("text", content="Hello world")
        response = mock_anthropic_response("tool_use", tool_name="web_search",
                                            tool_input={"query": "test"})
    """
    def _factory(
        kind: str = "text",
        *,
        content: str = "Mock response text.",
        tool_name: str = "web_search",
        tool_input: dict | None = None,
        tool_id: str = "toolu_001",
        input_tokens: int = 100,
        output_tokens: int = 50,
    ):
        response = MagicMock()
        response.usage = _make_usage(input_tokens, output_tokens)

        if kind == "text":
            response.stop_reason = "end_turn"
            response.content = [_make_text_block(content)]
        elif kind == "tool_use":
            response.stop_reason = "tool_use"
            response.content = [
                _make_tool_use_block(tool_name, tool_input or {}, tool_id),
            ]
        else:
            raise ValueError(f"Unknown response kind: {kind}")

        return response

    return _factory


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

@pytest.fixture
def tool_registry() -> ToolRegistry:
    """A ToolRegistry with a couple of mock tools registered."""
    registry = ToolRegistry()
    registry.register(
        name="echo",
        description="Echoes the input back.",
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        execute_fn=lambda text: f"echo: {text}",
    )
    registry.register(
        name="add",
        description="Adds two numbers.",
        input_schema={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
        },
        execute_fn=lambda a, b: str(a + b),
    )
    return registry
