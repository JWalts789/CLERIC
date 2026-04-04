"""Community source reputation system for tracking domain credibility.

Tracks which domains produce verified vs disputed claims across all
research pipeline runs, building a credibility score over time.
"""

import json
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone


class SourceReputation:
    """Tracks domain-level credibility scores across research runs.

    Each domain gets a score based on how often its claims are
    verified vs disputed/false across all pipeline runs.
    """

    def __init__(self, reputation_path: str = "data/source_reputation.json"):
        self.path = Path(reputation_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"domains": {}, "last_updated": None, "total_runs": 0}

    def _save(self):
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def _extract_domain(self, url: str) -> str | None:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else None
        except Exception:
            return None

    def update_from_pipeline(self, pipeline_result_dict: dict):
        """Extract source reputation data from a completed pipeline result.

        Looks at:
        - Researcher sources (which domains were cited)
        - Fact checker results (which claims from which domains were verified/disputed)
        """
        self.data["total_runs"] = self.data.get("total_runs", 0) + 1

        # Get researcher sources
        research_stage = pipeline_result_dict.get("stages", {}).get("research", {})
        research_data = research_stage.get("data", {})
        sources = research_data.get("sources", [])

        # Map URLs to domains
        source_domains = {}
        for source in sources:
            url = source.get("url", "")
            domain = self._extract_domain(url)
            if domain:
                source_domains[url] = domain
                # Track that this domain was cited
                if domain not in self.data["domains"]:
                    self.data["domains"][domain] = {
                        "cited_count": 0,
                        "verified_claims": 0,
                        "disputed_claims": 0,
                        "false_claims": 0,
                        "unverified_claims": 0,
                        "credibility_score": 0.5,  # neutral starting point
                    }
                self.data["domains"][domain]["cited_count"] += 1

        # Get fact checker results
        fc_stage = pipeline_result_dict.get("stages", {}).get("fact_checking", {})
        fc_data = fc_stage.get("data", {})
        claims = fc_data.get("verified_claims", [])

        for claim in claims:
            status = claim.get("status", "UNVERIFIED").upper()
            # Try to match claim to a source domain
            supporting = claim.get("supporting_sources", [])
            contradicting = claim.get("contradicting_sources", [])
            all_sources = supporting + contradicting

            for source_ref in all_sources:
                # source_ref might be a URL or a description
                domain = self._extract_domain(str(source_ref))
                if domain and domain in self.data["domains"]:
                    entry = self.data["domains"][domain]
                    if status == "VERIFIED":
                        entry["verified_claims"] += 1
                    elif status == "DISPUTED":
                        entry["disputed_claims"] += 1
                    elif status == "FALSE":
                        entry["false_claims"] += 1
                    else:
                        entry["unverified_claims"] += 1

        # Recalculate credibility scores
        for domain, entry in self.data["domains"].items():
            total = (
                entry["verified_claims"]
                + entry["disputed_claims"]
                + entry["false_claims"]
                + entry["unverified_claims"]
            )
            if total > 0:
                # Score: verified adds, false subtracts, disputed partially subtracts
                score = (
                    entry["verified_claims"] * 1.0
                    + entry["unverified_claims"] * 0.3
                    + entry["disputed_claims"] * -0.3
                    + entry["false_claims"] * -1.0
                ) / total
                # Normalize to 0-1 range
                entry["credibility_score"] = round(
                    max(0.0, min(1.0, (score + 1) / 2)), 3
                )
            # If only cited but no claims checked, score stays at 0.5

        self._save()

    def get_domain_score(self, url: str) -> dict | None:
        domain = self._extract_domain(url)
        if domain and domain in self.data["domains"]:
            return {"domain": domain, **self.data["domains"][domain]}
        return None

    def get_top_domains(self, limit: int = 20) -> list[dict]:
        """Return domains sorted by credibility score (highest first)."""
        return sorted(
            [{"domain": d, **v} for d, v in self.data["domains"].items()],
            key=lambda x: (-x["credibility_score"], -x["cited_count"]),
        )[:limit]

    def get_summary(self) -> dict:
        domains = self.data["domains"]
        return {
            "total_domains": len(domains),
            "total_runs": self.data["total_runs"],
            "last_updated": self.data["last_updated"],
            "avg_credibility": round(
                sum(d["credibility_score"] for d in domains.values()) / len(domains),
                3,
            )
            if domains
            else 0.5,
        }
