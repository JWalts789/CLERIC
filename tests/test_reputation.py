"""Tests for the SourceReputation system."""

import json
import tempfile
from pathlib import Path

import pytest

from cleric.reputation import SourceReputation


@pytest.fixture
def tmp_reputation(tmp_path):
    """Create a SourceReputation backed by a temporary file."""
    return SourceReputation(str(tmp_path / "source_reputation.json"))


@pytest.fixture
def mock_pipeline_result():
    """A realistic pipeline result dict with sources and fact-check claims."""
    return {
        "stages": {
            "research": {
                "data": {
                    "sources": [
                        {
                            "url": "https://www.reuters.com/article/climate-2024",
                            "title": "Climate Report 2024",
                            "claims": ["Global temps rose 1.2C"],
                        },
                        {
                            "url": "https://nature.com/studies/abc123",
                            "title": "Nature Study on CO2",
                            "claims": ["CO2 levels at 420ppm"],
                        },
                        {
                            "url": "https://www.bbc.com/news/science-12345",
                            "title": "BBC Science Coverage",
                            "claims": ["Sea levels rising"],
                        },
                        {
                            "url": "https://blog.example.com/hot-takes",
                            "title": "Random Blog",
                            "claims": ["Everything is fine"],
                        },
                    ],
                },
            },
            "fact_checking": {
                "data": {
                    "verified_claims": [
                        {
                            "claim": "Global temps rose 1.2C",
                            "status": "VERIFIED",
                            "supporting_sources": [
                                "https://www.reuters.com/article/climate-2024"
                            ],
                            "contradicting_sources": [],
                        },
                        {
                            "claim": "CO2 levels at 420ppm",
                            "status": "VERIFIED",
                            "supporting_sources": [
                                "https://nature.com/studies/abc123"
                            ],
                            "contradicting_sources": [],
                        },
                        {
                            "claim": "Sea levels rising",
                            "status": "DISPUTED",
                            "supporting_sources": [
                                "https://www.bbc.com/news/science-12345"
                            ],
                            "contradicting_sources": [],
                        },
                        {
                            "claim": "Everything is fine",
                            "status": "FALSE",
                            "supporting_sources": [],
                            "contradicting_sources": [
                                "https://blog.example.com/hot-takes"
                            ],
                        },
                    ],
                },
            },
        },
    }


class TestSourceReputationInit:
    def test_creates_file_on_save(self, tmp_path):
        path = tmp_path / "rep.json"
        rep = SourceReputation(str(path))
        assert not path.exists()  # not created until save
        rep.update_from_pipeline({"stages": {}})
        assert path.exists()

    def test_loads_empty_state(self, tmp_reputation):
        assert tmp_reputation.data["domains"] == {}
        assert tmp_reputation.data["total_runs"] == 0
        assert tmp_reputation.data["last_updated"] is None

    def test_loads_existing_data(self, tmp_path):
        path = tmp_path / "rep.json"
        existing = {
            "domains": {"example.com": {"cited_count": 5, "credibility_score": 0.8,
                                         "verified_claims": 3, "disputed_claims": 0,
                                         "false_claims": 0, "unverified_claims": 0}},
            "last_updated": "2026-01-01T00:00:00+00:00",
            "total_runs": 2,
        }
        path.write_text(json.dumps(existing), encoding="utf-8")
        rep = SourceReputation(str(path))
        assert rep.data["total_runs"] == 2
        assert "example.com" in rep.data["domains"]


class TestDomainExtraction:
    def test_basic_url(self, tmp_reputation):
        assert tmp_reputation._extract_domain("https://reuters.com/article") == "reuters.com"

    def test_www_prefix_stripped(self, tmp_reputation):
        assert tmp_reputation._extract_domain("https://www.reuters.com/article") == "reuters.com"

    def test_subdomain_preserved(self, tmp_reputation):
        assert tmp_reputation._extract_domain("https://news.bbc.co.uk/story") == "news.bbc.co.uk"

    def test_empty_string(self, tmp_reputation):
        assert tmp_reputation._extract_domain("") is None

    def test_invalid_url(self, tmp_reputation):
        assert tmp_reputation._extract_domain("not a url at all") is None

    def test_no_scheme(self, tmp_reputation):
        # urlparse without scheme puts everything in path
        assert tmp_reputation._extract_domain("reuters.com/article") is None

    def test_case_normalized(self, tmp_reputation):
        assert tmp_reputation._extract_domain("https://Reuters.COM/article") == "reuters.com"


class TestUpdateFromPipeline:
    def test_increments_total_runs(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["total_runs"] == 1
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["total_runs"] == 2

    def test_tracks_cited_domains(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        domains = tmp_reputation.data["domains"]
        assert "reuters.com" in domains
        assert "nature.com" in domains
        assert "bbc.com" in domains
        assert "blog.example.com" in domains

    def test_cited_count(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["domains"]["reuters.com"]["cited_count"] == 1
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["domains"]["reuters.com"]["cited_count"] == 2

    def test_verified_claims_counted(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["domains"]["reuters.com"]["verified_claims"] == 1
        assert tmp_reputation.data["domains"]["nature.com"]["verified_claims"] == 1

    def test_disputed_claims_counted(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["domains"]["bbc.com"]["disputed_claims"] == 1

    def test_false_claims_counted(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["domains"]["blog.example.com"]["false_claims"] == 1

    def test_saves_file(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.path.exists()
        loaded = json.loads(tmp_reputation.path.read_text(encoding="utf-8"))
        assert loaded["total_runs"] == 1
        assert "reuters.com" in loaded["domains"]

    def test_last_updated_set(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        assert tmp_reputation.data["last_updated"] is not None

    def test_empty_pipeline_result(self, tmp_reputation):
        tmp_reputation.update_from_pipeline({"stages": {}})
        assert tmp_reputation.data["total_runs"] == 1
        assert tmp_reputation.data["domains"] == {}

    def test_missing_stages(self, tmp_reputation):
        tmp_reputation.update_from_pipeline({})
        assert tmp_reputation.data["total_runs"] == 1


class TestCredibilityScoreCalculation:
    def test_verified_only_gives_high_score(self, tmp_reputation):
        result = {
            "stages": {
                "research": {
                    "data": {
                        "sources": [
                            {"url": "https://good.org/page", "title": "Good"},
                        ],
                    },
                },
                "fact_checking": {
                    "data": {
                        "verified_claims": [
                            {
                                "claim": "Claim A",
                                "status": "VERIFIED",
                                "supporting_sources": ["https://good.org/page"],
                                "contradicting_sources": [],
                            },
                        ],
                    },
                },
            },
        }
        tmp_reputation.update_from_pipeline(result)
        score = tmp_reputation.data["domains"]["good.org"]["credibility_score"]
        assert score == 1.0  # (1.0 + 1) / 2 = 1.0

    def test_false_only_gives_low_score(self, tmp_reputation):
        result = {
            "stages": {
                "research": {
                    "data": {
                        "sources": [
                            {"url": "https://bad.org/page", "title": "Bad"},
                        ],
                    },
                },
                "fact_checking": {
                    "data": {
                        "verified_claims": [
                            {
                                "claim": "Claim B",
                                "status": "FALSE",
                                "supporting_sources": [],
                                "contradicting_sources": ["https://bad.org/page"],
                            },
                        ],
                    },
                },
            },
        }
        tmp_reputation.update_from_pipeline(result)
        score = tmp_reputation.data["domains"]["bad.org"]["credibility_score"]
        assert score == 0.0  # (-1.0 + 1) / 2 = 0.0

    def test_mixed_gives_moderate_score(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        # bbc.com has 1 disputed claim -> score = (-0.3 + 1) / 2 = 0.35
        score = tmp_reputation.data["domains"]["bbc.com"]["credibility_score"]
        assert 0.3 <= score <= 0.4

    def test_unchecked_domain_stays_neutral(self, tmp_reputation):
        result = {
            "stages": {
                "research": {
                    "data": {
                        "sources": [
                            {"url": "https://neutral.org/page", "title": "Neutral"},
                        ],
                    },
                },
                "fact_checking": {"data": {"verified_claims": []}},
            },
        }
        tmp_reputation.update_from_pipeline(result)
        score = tmp_reputation.data["domains"]["neutral.org"]["credibility_score"]
        assert score == 0.5

    def test_score_clamped_to_0_1(self, tmp_reputation):
        """Scores should never exceed 0-1 range."""
        result = {
            "stages": {
                "research": {
                    "data": {
                        "sources": [
                            {"url": "https://test.org/page", "title": "Test"},
                        ],
                    },
                },
                "fact_checking": {
                    "data": {
                        "verified_claims": [
                            {
                                "claim": f"Claim {i}",
                                "status": "VERIFIED",
                                "supporting_sources": ["https://test.org/page"],
                                "contradicting_sources": [],
                            }
                            for i in range(10)
                        ],
                    },
                },
            },
        }
        tmp_reputation.update_from_pipeline(result)
        score = tmp_reputation.data["domains"]["test.org"]["credibility_score"]
        assert 0.0 <= score <= 1.0


class TestGetTopDomains:
    def test_sorted_by_credibility(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        top = tmp_reputation.get_top_domains()
        scores = [d["credibility_score"] for d in top]
        assert scores == sorted(scores, reverse=True)

    def test_limit_respected(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        top = tmp_reputation.get_top_domains(limit=2)
        assert len(top) == 2

    def test_returns_domain_key(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        top = tmp_reputation.get_top_domains()
        assert all("domain" in d for d in top)

    def test_empty_returns_empty(self, tmp_reputation):
        assert tmp_reputation.get_top_domains() == []


class TestGetDomainScore:
    def test_known_domain(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        result = tmp_reputation.get_domain_score("https://reuters.com/anything")
        assert result is not None
        assert result["domain"] == "reuters.com"
        assert "credibility_score" in result

    def test_unknown_domain(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        result = tmp_reputation.get_domain_score("https://unknown.org/page")
        assert result is None

    def test_www_prefix_handled(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        result = tmp_reputation.get_domain_score("https://www.reuters.com/other")
        assert result is not None
        assert result["domain"] == "reuters.com"


class TestGetSummary:
    def test_empty_summary(self, tmp_reputation):
        summary = tmp_reputation.get_summary()
        assert summary["total_domains"] == 0
        assert summary["total_runs"] == 0
        assert summary["avg_credibility"] == 0.5

    def test_populated_summary(self, tmp_reputation, mock_pipeline_result):
        tmp_reputation.update_from_pipeline(mock_pipeline_result)
        summary = tmp_reputation.get_summary()
        assert summary["total_domains"] == 4
        assert summary["total_runs"] == 1
        assert summary["last_updated"] is not None
        assert 0.0 <= summary["avg_credibility"] <= 1.0
