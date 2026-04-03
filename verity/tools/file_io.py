"""File I/O tools for reading and writing local files.

Used by agents to persist memory, write research output,
and read previously saved data.
"""

from pathlib import Path


READ_FILE_SCHEMA: dict = {
    "name": "read_file",
    "description": (
        "Read the contents of a local file. Use this to load previously saved "
        "research, memory files, or other text data."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to read from.",
            },
        },
        "required": ["path"],
    },
}

WRITE_FILE_SCHEMA: dict = {
    "name": "write_file",
    "description": (
        "Write content to a local file. Creates parent directories if needed. "
        "Use this to save research output, reports, or memory data."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to write to.",
            },
            "content": {
                "type": "string",
                "description": "The text content to write.",
            },
        },
        "required": ["path", "content"],
    },
}


def read_file(path: str) -> str:
    """Read and return the contents of a file.

    Args:
        path: The file path to read.

    Returns:
        The file contents as a string, or an error message on failure.
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"File not found: {path}"
        if not file_path.is_file():
            return f"Not a file: {path}"
        return file_path.read_text(encoding="utf-8")
    except PermissionError:
        return f"Permission denied: {path}"
    except Exception as e:
        return f"Error reading {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: The file path to write to.
        content: The text content to write.

    Returns:
        A confirmation message with the file path and bytes written,
        or an error message on failure.
    """
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {path}"
    except PermissionError:
        return f"Permission denied: {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"
