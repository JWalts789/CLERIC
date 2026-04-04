"""Tests for cleric.tools.web_fetch — page fetching and text extraction."""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import httpx

from cleric.tools.web_fetch import fetch_page, _make_request, FETCH_PAGE_SCHEMA


class TestFetchPageSchema:
    """Verify the tool schema."""

    def test_schema_has_required_fields(self):
        assert FETCH_PAGE_SCHEMA["name"] == "fetch_page"
        assert "url" in FETCH_PAGE_SCHEMA["input_schema"]["properties"]

    def test_url_is_required(self):
        assert "url" in FETCH_PAGE_SCHEMA["input_schema"]["required"]


class TestFetchPage:
    """Test fetch_page with mocked HTTP responses."""

    @patch("cleric.tools.web_fetch._make_request")
    def test_extracts_text_from_html(self, mock_request):
        html = "<html><body><main><p>Hello world</p></main></body></html>"
        mock_response = MagicMock()
        mock_response.text = html
        mock_request.return_value = mock_response

        result = fetch_page("https://example.com")
        assert "Hello world" in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_strips_noise_tags(self, mock_request):
        html = """<html><body>
            <nav>Navigation stuff</nav>
            <script>var x = 1;</script>
            <main><p>Actual content</p></main>
            <footer>Footer stuff</footer>
        </body></html>"""
        mock_response = MagicMock()
        mock_response.text = html
        mock_request.return_value = mock_response

        result = fetch_page("https://example.com")
        assert "Actual content" in result
        assert "Navigation stuff" not in result
        assert "var x = 1" not in result
        assert "Footer stuff" not in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_truncates_to_max_length(self, mock_request):
        html = f"<html><body><p>{'A' * 5000}</p></body></html>"
        mock_response = MagicMock()
        mock_response.text = html
        mock_request.return_value = mock_response

        result = fetch_page("https://example.com", max_length=100)
        assert len(result) <= 100 + len("\n\n[...truncated]")
        assert "[...truncated]" in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_http_403_returns_access_denied(self, mock_request):
        error_response = MagicMock()
        error_response.status_code = 403
        mock_request.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=error_response
        )

        result = fetch_page("https://blocked.com")
        assert "Access denied (403)" in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_http_500_returns_error(self, mock_request):
        error_response = MagicMock()
        error_response.status_code = 500
        mock_request.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=error_response
        )

        result = fetch_page("https://broken.com")
        assert "HTTP error" in result
        assert "500" in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_timeout_returns_error(self, mock_request):
        mock_request.side_effect = httpx.RequestError(
            "Timed out", request=MagicMock()
        )

        result = fetch_page("https://slow.com")
        assert "Request failed" in result

    def test_wikipedia_url_blocked(self):
        result = fetch_page("https://en.wikipedia.org/wiki/Test")
        assert "Wikipedia is blocked" in result

    def test_wikipedia_url_blocked_case_insensitive(self):
        result = fetch_page("https://en.WIKIPEDIA.ORG/wiki/Test")
        assert "Wikipedia is blocked" in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_uses_article_tag_when_no_main(self, mock_request):
        html = "<html><body><article><p>Article content</p></article></body></html>"
        mock_response = MagicMock()
        mock_response.text = html
        mock_request.return_value = mock_response

        result = fetch_page("https://example.com")
        assert "Article content" in result

    @patch("cleric.tools.web_fetch._make_request")
    def test_falls_back_to_body(self, mock_request):
        html = "<html><body><p>Body content here</p></body></html>"
        mock_response = MagicMock()
        mock_response.text = html
        mock_request.return_value = mock_response

        result = fetch_page("https://example.com")
        assert "Body content here" in result


class TestMakeRequest:
    """Test the _make_request retry logic."""

    @patch("cleric.tools.web_fetch.time.sleep")
    @patch("cleric.tools.web_fetch.httpx.get")
    @patch("cleric.tools.web_fetch.random.choice", return_value="TestAgent/1.0")
    def test_successful_request(self, mock_choice, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _make_request("https://example.com")
        assert result == mock_response
        mock_sleep.assert_not_called()

    @patch("cleric.tools.web_fetch.time.sleep")
    @patch("cleric.tools.web_fetch.httpx.get")
    @patch("cleric.tools.web_fetch.random.choice", return_value="TestAgent/1.0")
    def test_retries_on_500_then_succeeds(self, mock_choice, mock_get, mock_sleep):
        error_response = MagicMock()
        error_response.status_code = 500
        error = httpx.HTTPStatusError("Server Error", request=MagicMock(), response=error_response)

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()

        mock_get.side_effect = [MagicMock(raise_for_status=MagicMock(side_effect=error)), success_response]

        # The first call raises via raise_for_status; need to set it up properly
        first_response = MagicMock()
        first_response.raise_for_status.side_effect = error
        second_response = MagicMock()
        second_response.raise_for_status = MagicMock()

        mock_get.side_effect = [first_response, second_response]

        result = _make_request("https://example.com")
        assert result == second_response
        assert mock_sleep.call_count == 1

    @patch("cleric.tools.web_fetch.time.sleep")
    @patch("cleric.tools.web_fetch.httpx.get")
    @patch("cleric.tools.web_fetch.random.choice", return_value="TestAgent/1.0")
    def test_403_raises_immediately_no_retry(self, mock_choice, mock_get, mock_sleep):
        error_response = MagicMock()
        error_response.status_code = 403
        error = httpx.HTTPStatusError("Forbidden", request=MagicMock(), response=error_response)

        first_response = MagicMock()
        first_response.raise_for_status.side_effect = error
        mock_get.return_value = first_response

        with pytest.raises(httpx.HTTPStatusError):
            _make_request("https://blocked.com")

        mock_sleep.assert_not_called()

    @patch("cleric.tools.web_fetch.time.sleep")
    @patch("cleric.tools.web_fetch.httpx.get")
    @patch("cleric.tools.web_fetch.random.choice", return_value="TestAgent/1.0")
    def test_retries_on_connection_error_then_succeeds(self, mock_choice, mock_get, mock_sleep):
        conn_error = httpx.RequestError("Connection reset", request=MagicMock())

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()

        mock_get.side_effect = [conn_error, success_response]

        result = _make_request("https://example.com")
        assert result == success_response
        assert mock_sleep.call_count == 1

    @patch("cleric.tools.web_fetch.time.sleep")
    @patch("cleric.tools.web_fetch.httpx.get")
    @patch("cleric.tools.web_fetch.random.choice", return_value="TestAgent/1.0")
    def test_rotating_user_agent(self, mock_choice, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        _make_request("https://example.com")

        # Verify random.choice was called to select a user agent
        mock_choice.assert_called_once()
        # Verify the User-Agent header was set
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["headers"]["User-Agent"] == "TestAgent/1.0"

    @patch("cleric.tools.web_fetch.time.sleep")
    @patch("cleric.tools.web_fetch.httpx.get")
    @patch("cleric.tools.web_fetch.random.choice", return_value="TestAgent/1.0")
    def test_exhausted_retries_raises(self, mock_choice, mock_get, mock_sleep):
        conn_error = httpx.RequestError("Connection reset", request=MagicMock())
        mock_get.side_effect = conn_error

        with pytest.raises(httpx.RequestError):
            _make_request("https://example.com")

        # MAX_RETRIES is 2, so sleep called twice (attempts 0, 1 retry, 2 retry then raise)
        assert mock_sleep.call_count == 2
