"""Tool registry for managing agent-callable tools.

Provides a central registry that stores tool schemas (for Claude API)
alongside their Python implementations, enabling dynamic tool use.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from cleric.tools.web_search import search_web, SEARCH_WEB_SCHEMA
from cleric.tools.web_fetch import fetch_page, FETCH_PAGE_SCHEMA
from cleric.tools.file_io import read_file, write_file, READ_FILE_SCHEMA, WRITE_FILE_SCHEMA


@dataclass
class RegisteredTool:
    """A tool registered in the system with its schema and implementation."""

    name: str
    description: str
    input_schema: dict[str, Any]
    execute: Callable[..., str]

    @property
    def schema(self) -> dict[str, Any]:
        """Return the Claude API tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    """Registry mapping tool names to their schemas and implementations.

    Tools are registered with a name, description, JSON Schema for inputs,
    and a callable that executes the tool. The registry provides schemas
    in Claude API format and dispatches execution by name.
    """

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        execute_fn: Callable[..., str],
    ) -> None:
        """Register a tool with its schema and implementation.

        Args:
            name: Unique tool identifier.
            description: Human-readable description for the LLM.
            input_schema: JSON Schema describing the tool's input parameters.
            execute_fn: Callable that accepts keyword arguments matching
                        the input_schema and returns a string result.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")

        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            input_schema=input_schema,
            execute=execute_fn,
        )

    def get_schemas(self) -> list[dict[str, Any]]:
        """Return all tool schemas in Claude API format.

        Returns:
            List of tool schema dicts suitable for the Anthropic API tools parameter.
        """
        return [tool.schema for tool in self._tools.values()]

    def execute(self, name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool by name with the given input.

        Args:
            name: The registered tool name.
            tool_input: Dictionary of input parameters matching the tool's schema.

        Returns:
            String result from the tool execution.

        Raises:
            KeyError: If no tool with the given name is registered.
        """
        if name not in self._tools:
            raise KeyError(
                f"Unknown tool '{name}'. Available: {list(self._tools.keys())}"
            )
        return self._tools[name].execute(**tool_input)

    @property
    def tool_names(self) -> list[str]:
        """Return the names of all registered tools."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


def create_default_registry() -> ToolRegistry:
    """Create a ToolRegistry pre-loaded with all built-in tools.

    Returns:
        A ToolRegistry with web_search, fetch_page, read_file, and write_file
        registered and ready to use.
    """
    registry = ToolRegistry()

    registry.register(
        name=SEARCH_WEB_SCHEMA["name"],
        description=SEARCH_WEB_SCHEMA["description"],
        input_schema=SEARCH_WEB_SCHEMA["input_schema"],
        execute_fn=search_web,
    )

    registry.register(
        name=FETCH_PAGE_SCHEMA["name"],
        description=FETCH_PAGE_SCHEMA["description"],
        input_schema=FETCH_PAGE_SCHEMA["input_schema"],
        execute_fn=fetch_page,
    )

    registry.register(
        name=READ_FILE_SCHEMA["name"],
        description=READ_FILE_SCHEMA["description"],
        input_schema=READ_FILE_SCHEMA["input_schema"],
        execute_fn=read_file,
    )

    registry.register(
        name=WRITE_FILE_SCHEMA["name"],
        description=WRITE_FILE_SCHEMA["description"],
        input_schema=WRITE_FILE_SCHEMA["input_schema"],
        execute_fn=write_file,
    )

    return registry
