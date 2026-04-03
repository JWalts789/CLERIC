"""Tests for cleric.config.Config."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from cleric.config import Config


class TestConfigDirect:
    """Test constructing Config directly."""

    def test_valid_config(self, tmp_path: Path):
        cfg = Config(
            anthropic_api_key="sk-test-123",
            memory_dir=tmp_path / "mem",
            output_dir=tmp_path / "out",
        )
        assert cfg.anthropic_api_key == "sk-test-123"
        assert cfg.model == "claude-sonnet-4-6"
        assert cfg.max_tokens == 4096

    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            Config(anthropic_api_key="")

    def test_default_values(self):
        cfg = Config(anthropic_api_key="sk-test")
        assert cfg.max_search_results == 10
        assert cfg.max_tokens == 4096
        assert cfg.memory_dir == Path("./memory_store")
        assert cfg.output_dir == Path("./output")

    def test_ensure_directories(self, tmp_path: Path):
        cfg = Config(
            anthropic_api_key="sk-test",
            memory_dir=tmp_path / "a" / "b",
            output_dir=tmp_path / "c" / "d",
        )
        cfg.ensure_directories()
        assert cfg.memory_dir.is_dir()
        assert cfg.output_dir.is_dir()


class TestConfigFromEnv:
    """Test Config.from_env() loading from environment."""

    def test_loads_api_key_from_env(self, tmp_path: Path):
        env = {
            "ANTHROPIC_API_KEY": "sk-from-env",
            "CLERIC_MODEL": "claude-test-model",
            "CLERIC_MAX_SEARCH_RESULTS": "20",
            "CLERIC_MEMORY_DIR": str(tmp_path / "mem"),
            "CLERIC_OUTPUT_DIR": str(tmp_path / "out"),
            "CLERIC_MAX_TOKENS": "2048",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = Config.from_env(dotenv_path="/dev/null")

        assert cfg.anthropic_api_key == "sk-from-env"
        assert cfg.model == "claude-test-model"
        assert cfg.max_search_results == 20
        assert cfg.max_tokens == 2048

    def test_missing_env_key_raises(self):
        env = {"ANTHROPIC_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(ValueError):
                Config.from_env(dotenv_path="/dev/null")

    def test_defaults_when_env_unset(self):
        env = {"ANTHROPIC_API_KEY": "sk-test"}
        # Clear CLERIC_* vars to ensure defaults
        cleared = {k: "" for k in os.environ if k.startswith("CLERIC_")}
        with patch.dict(os.environ, {**cleared, **env}, clear=False):
            cfg = Config.from_env(dotenv_path="/dev/null")

        assert cfg.model == "claude-sonnet-4-6"
        assert cfg.max_search_results == 10
