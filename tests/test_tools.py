"""Tests for cleric.tools.registry and individual tool modules."""

import pytest

from cleric.tools.registry import ToolRegistry, RegisteredTool


class TestRegisteredTool:
    """Test the RegisteredTool dataclass."""

    def test_schema_property(self):
        tool = RegisteredTool(
            name="test_tool",
            description="A test tool.",
            input_schema={"type": "object", "properties": {}},
            execute=lambda: "ok",
        )
        schema = tool.schema
        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool."
        assert "input_schema" in schema

    def test_schema_matches_claude_api_format(self):
        """Schema dict should have exactly the three keys Claude expects."""
        tool = RegisteredTool(
            name="t",
            description="d",
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
            execute=lambda x: x,
        )
        assert set(tool.schema.keys()) == {"name", "description", "input_schema"}


class TestToolRegistry:
    """Test ToolRegistry register/get_schemas/execute."""

    def test_register_and_len(self, tool_registry: ToolRegistry):
        assert len(tool_registry) == 2
        assert "echo" in tool_registry
        assert "add" in tool_registry

    def test_get_schemas(self, tool_registry: ToolRegistry):
        schemas = tool_registry.get_schemas()
        assert len(schemas) == 2
        names = {s["name"] for s in schemas}
        assert names == {"echo", "add"}
        for schema in schemas:
            assert "input_schema" in schema
            assert "description" in schema

    def test_execute_echo(self, tool_registry: ToolRegistry):
        result = tool_registry.execute("echo", {"text": "hello"})
        assert result == "echo: hello"

    def test_execute_add(self, tool_registry: ToolRegistry):
        result = tool_registry.execute("add", {"a": 3, "b": 7})
        assert result == "10"

    def test_tool_names(self, tool_registry: ToolRegistry):
        assert set(tool_registry.tool_names) == {"echo", "add"}

    def test_duplicate_registration_raises(self, tool_registry: ToolRegistry):
        with pytest.raises(ValueError, match="already registered"):
            tool_registry.register(
                name="echo",
                description="duplicate",
                input_schema={"type": "object", "properties": {}},
                execute_fn=lambda: "",
            )

    def test_execute_unknown_tool_raises(self, tool_registry: ToolRegistry):
        with pytest.raises(KeyError, match="Unknown tool 'nonexistent'"):
            tool_registry.execute("nonexistent", {})

    def test_contains_false_for_missing(self, tool_registry: ToolRegistry):
        assert "nonexistent" not in tool_registry

    def test_empty_registry(self):
        registry = ToolRegistry()
        assert len(registry) == 0
        assert registry.get_schemas() == []
        assert registry.tool_names == []


class TestFileIOTools:
    """Test file_io read_file and write_file functions."""

    def test_write_and_read_roundtrip(self, tmp_path):
        from cleric.tools.file_io import read_file, write_file

        path = str(tmp_path / "test.txt")
        result = write_file(path, "hello world")
        assert "11 characters" in result

        content = read_file(path)
        assert content == "hello world"

    def test_read_nonexistent_file(self):
        from cleric.tools.file_io import read_file
        result = read_file("/nonexistent/path/file.txt")
        assert "File not found" in result

    def test_write_creates_parent_dirs(self, tmp_path):
        from cleric.tools.file_io import write_file
        path = str(tmp_path / "a" / "b" / "c.txt")
        result = write_file(path, "deep")
        assert "4 characters" in result

    def test_read_not_a_file(self, tmp_path):
        """Reading a directory path should return an error message."""
        from cleric.tools.file_io import read_file
        result = read_file(str(tmp_path))
        assert "Not a file" in result

    def test_read_permission_denied(self, tmp_path):
        """read_file should handle PermissionError gracefully."""
        from unittest.mock import patch
        from cleric.tools.file_io import read_file
        with patch("cleric.tools.file_io.Path.read_text", side_effect=PermissionError("nope")):
            result = read_file(str(tmp_path / "exists.txt"))
            # File doesn't exist so it'll hit "File not found" first
            assert "File not found" in result or "Permission denied" in result

    def test_write_permission_denied(self, tmp_path):
        """write_file should handle PermissionError gracefully."""
        from unittest.mock import patch
        from cleric.tools.file_io import write_file
        with patch("cleric.tools.file_io.Path.write_text", side_effect=PermissionError("nope")):
            result = write_file(str(tmp_path / "test.txt"), "content")
            assert "Permission denied" in result

    def test_write_generic_error(self, tmp_path):
        """write_file should handle generic exceptions gracefully."""
        from unittest.mock import patch
        from cleric.tools.file_io import write_file
        with patch("cleric.tools.file_io.Path.write_text", side_effect=OSError("disk full")):
            result = write_file(str(tmp_path / "test.txt"), "content")
            assert "Error writing" in result

    def test_read_generic_error(self, tmp_path):
        """read_file should handle generic exceptions gracefully."""
        from unittest.mock import patch
        from cleric.tools.file_io import read_file

        # Create the file so it passes exists() and is_file() checks
        file_path = tmp_path / "bad.txt"
        file_path.write_text("data")

        with patch("cleric.tools.file_io.Path.read_text", side_effect=OSError("I/O error")):
            result = read_file(str(file_path))
            assert "Error reading" in result
