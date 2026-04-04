"""Tests for cleric.tools.web_search — DuckDuckGo search tool."""

from unittest.mock import MagicMock, patch

import pytest

from cleric.tools.web_search import search_web, SEARCH_WEB_SCHEMA


class TestSearchWebSchema:
    """Verify the tool schema is well-formed."""

    def test_schema_has_required_fields(self):
        assert SEARCH_WEB_SCHEMA["name"] == "web_search"
        assert "input_schema" in SEARCH_WEB_SCHEMA
        assert "query" in SEARCH_WEB_SCHEMA["input_schema"]["properties"]

    def test_query_is_required(self):
        assert "query" in SEARCH_WEB_SCHEMA["input_schema"]["required"]


class TestSearchWeb:
    """Test the search_web function with mocked DDGS."""

    def _mock_ddgs(self, results):
        """Create a mock DDGS context manager returning given results."""
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = results
        mock_ddgs_cls = MagicMock()
        mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs_instance)
        mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
        return mock_ddgs_cls

    @patch("cleric.tools.web_search.DDGS")
    def test_returns_formatted_results(self, MockDDGS):
        results = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Snippet 2"},
        ]
        mock_instance = MagicMock()
        mock_instance.text.return_value = results
        MockDDGS.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)

        output = search_web("test query", max_results=5)

        assert "[1] Result 1" in output
        assert "https://example.com/1" in output
        assert "Snippet 1" in output
        assert "[2] Result 2" in output

    @patch("cleric.tools.web_search.DDGS")
    def test_empty_results_returns_no_results_message(self, MockDDGS):
        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        MockDDGS.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)

        output = search_web("obscure query", max_results=5)
        assert "No results found" in output

    @patch("cleric.tools.web_search.DDGS")
    def test_exception_returns_error_message(self, MockDDGS):
        MockDDGS.return_value.__enter__ = MagicMock(
            side_effect=RuntimeError("Connection failed")
        )
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)

        output = search_web("fail query")
        assert "Search failed" in output

    @patch("cleric.tools.web_search.DDGS")
    def test_wikipedia_results_are_filtered(self, MockDDGS):
        results = [
            {"title": "Wiki Page", "href": "https://en.wikipedia.org/wiki/Test", "body": "Wiki"},
            {"title": "Good Source", "href": "https://reuters.com/article", "body": "Real news"},
        ]
        mock_instance = MagicMock()
        mock_instance.text.return_value = results
        MockDDGS.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)

        output = search_web("test query", max_results=5)
        assert "wikipedia.org" not in output
        assert "Good Source" in output

    @patch("cleric.tools.web_search.DDGS")
    def test_max_results_respected(self, MockDDGS):
        results = [
            {"title": f"Result {i}", "href": f"https://example.com/{i}", "body": f"Snippet {i}"}
            for i in range(20)
        ]
        mock_instance = MagicMock()
        mock_instance.text.return_value = results
        MockDDGS.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)

        output = search_web("test", max_results=3)
        # Should have at most 3 numbered results
        assert "[3]" in output
        assert "[4]" not in output

    @patch("cleric.tools.web_search.DDGS")
    def test_missing_fields_use_defaults(self, MockDDGS):
        """Results missing title/href/body should use fallback text."""
        results = [
            {"title": None, "href": None, "body": None},
        ]
        # get() returns None for these, so the fallback "No title" etc. won't trigger
        # But the function should not crash
        mock_instance = MagicMock()
        mock_instance.text.return_value = [{}]  # empty dicts
        MockDDGS.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)

        output = search_web("test", max_results=5)
        assert "No title" in output
        assert "No URL" in output
