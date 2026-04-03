"""Configuration management for Verity.

Loads settings from environment variables with sensible defaults.
Uses python-dotenv to support .env files.
"""

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os


@dataclass
class Config:
    """Immutable application configuration loaded from environment variables.

    All VERITY_* env vars map to fields with the prefix stripped and lowercased.
    ANTHROPIC_API_KEY is the only required variable.
    """

    anthropic_api_key: str
    model: str = "claude-sonnet-4-6"
    max_search_results: int = 10
    memory_dir: Path = field(default_factory=lambda: Path("./memory_store"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    max_tokens: int = 4096

    def __post_init__(self) -> None:
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. "
                "Set it in your environment or in a .env file."
            )

    @classmethod
    def from_env(cls, dotenv_path: str | Path | None = None) -> "Config":
        """Load configuration from environment variables.

        Args:
            dotenv_path: Optional path to a .env file. Defaults to .env in cwd.

        Returns:
            A populated Config instance.
        """
        load_dotenv(dotenv_path)

        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("VERITY_MODEL", "claude-sonnet-4-6"),
            max_search_results=int(os.getenv("VERITY_MAX_SEARCH_RESULTS", "10")),
            memory_dir=Path(os.getenv("VERITY_MEMORY_DIR", "./memory_store")),
            output_dir=Path(os.getenv("VERITY_OUTPUT_DIR", "./output")),
            max_tokens=int(os.getenv("VERITY_MAX_TOKENS", "4096")),
        )

    def ensure_directories(self) -> None:
        """Create memory and output directories if they don't exist."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
