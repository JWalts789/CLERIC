"""Markdown report generator for research pipeline results."""

from pathlib import Path
from datetime import datetime, timezone

from cleric.orchestrator import PipelineResult


class ReportGenerator:
    """Generates comprehensive markdown reports from pipeline results."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, result: PipelineResult) -> Path:
        """Generate a full markdown research report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = self._slugify(result.query)
        filename = f"{timestamp}_{slug}_report.md"
        path = self.output_dir / filename

        sections = [
            self._header(result),
            self._bias_section(result),
            self._research_section(result),
            self._factcheck_section(result),
            self._challenges_section(result),
            self._final_report_section(result),
            self._evaluation_section(result),
            self._metadata_section(result),
        ]

        path.write_text("\n\n---\n\n".join(sections), encoding="utf-8")
        return path

    def _header(self, result: PipelineResult) -> str:
        grade = result.overall_grade or "N/A"
        return f"""# C.L.E.R.I.C. Research Report

**Query:** {result.query}
**Date:** {result.timestamp}
**Grade:** {grade}
**Duration:** {result.duration_seconds:.1f}s
**Tokens Used:** {result.total_tokens['input'] + result.total_tokens['output']:,}"""

    def _bias_section(self, result: PipelineResult) -> str:
        stage = result.stages.get("bias_detection")
        if not stage:
            return "## 1. Bias Analysis\n\n*No bias analysis performed.*"

        data = stage.data
        score = data.get("bias_score", "N/A")
        biases = data.get("detected_biases", [])
        neutral = data.get("neutral_queries", [])
        perspectives = data.get("required_perspectives", [])

        bias_list = "\n".join(f"- {b}" for b in biases) if biases else "- None detected"
        neutral_list = "\n".join(f"- {q}" for q in neutral) if neutral else "- Original query used"
        persp_list = "\n".join(f"- {p}" for p in perspectives) if perspectives else "- General"

        return f"""## 1. Bias Analysis

**Bias Score:** {score}/10

### Detected Biases
{bias_list}

### Neutral Reformulations
{neutral_list}

### Required Perspectives
{persp_list}"""

    def _research_section(self, result: PipelineResult) -> str:
        stage = result.stages.get("research")
        if not stage:
            return "## 2. Research Findings\n\n*No research performed.*"

        sources = stage.data.get("sources", [])
        tool_count = len(stage.tool_calls_made)

        source_entries = ""
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            perspective = source.get("perspective", "neutral")
            claims = source.get("claims", [])
            claims_text = "\n".join(f"  - {c}" for c in claims[:5])
            source_entries += f"""
### Source {i}: {title}
- **URL:** {url}
- **Perspective:** {perspective}
- **Key Claims:**
{claims_text}
"""

        return f"""## 2. Research Findings

**Sources Found:** {len(sources)} | **Tool Calls:** {tool_count}

{source_entries}"""

    def _factcheck_section(self, result: PipelineResult) -> str:
        stage = result.stages.get("fact_checking")
        if not stage:
            return "## 3. Fact Verification\n\n*No fact checking performed.*"

        claims = stage.data.get("verified_claims", stage.data.get("claims", []))
        tool_count = len(stage.tool_calls_made)

        # Summary
        counts: dict[str, int] = {}
        for claim in claims:
            s = str(claim.get("status", "UNVERIFIED")).upper()
            counts[s] = counts.get(s, 0) + 1

        summary = " | ".join(f"**{k}:** {v}" for k, v in counts.items())

        claim_entries = ""
        for claim in claims:
            text = claim.get("claim", "")
            status = claim.get("status", "UNVERIFIED")
            confidence = claim.get("confidence", 0)
            supporting = claim.get("supporting_sources", [])
            contradicting = claim.get("contradicting_sources", [])

            icon = {"VERIFIED": "✅", "DISPUTED": "⚠️", "UNVERIFIED": "❓", "FALSE": "❌"}.get(
                status, "❓"
            )
            claim_entries += f"\n{icon} **{text}**\n- Status: {status} | Confidence: {confidence:.0%}\n"
            if supporting:
                claim_entries += f"- Supporting: {', '.join(str(s) for s in supporting[:3])}\n"
            if contradicting:
                claim_entries += f"- Contradicting: {', '.join(str(s) for s in contradicting[:3])}\n"

        return f"""## 3. Fact Verification

{summary} | **Tool Calls:** {tool_count}

{claim_entries}"""

    def _challenges_section(self, result: PipelineResult) -> str:
        stage = result.stages.get("devils_advocate")
        if not stage:
            return "## 4. Adversarial Challenges\n\n*No challenges raised.*"

        challenges = stage.data.get("challenges", [])
        if not challenges:
            return f"## 4. Adversarial Challenges\n\n{stage.content}"

        entries = ""
        for challenge in challenges:
            text = challenge.get("challenge", "")
            severity = challenge.get("severity", "medium")
            ctype = challenge.get("type", "general")
            rec = challenge.get("recommendation", "")
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            entries += f"\n{icon} **[{severity.upper()}] {ctype}:** {text}\n- Recommendation: {rec}\n"

        return f"""## 4. Adversarial Challenges

**Challenges Raised:** {len(challenges)}

{entries}"""

    def _final_report_section(self, result: PipelineResult) -> str:
        return f"""## 5. Synthesized Report

{result.final_report}"""

    def _evaluation_section(self, result: PipelineResult) -> str:
        stage = result.stages.get("evaluation")
        if not stage:
            return "## 6. Quality Evaluation\n\n*No evaluation performed.*"

        scores = stage.data.get("scores", {})
        grade = stage.data.get("grade", "N/A")
        improvements = stage.data.get("improvements", [])

        score_rows = ""
        for metric, score in scores.items():
            if isinstance(score, (int, float)):
                label = metric.replace("_", " ").title()
                bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                score_rows += f"| {label} | {bar} | {score:.0%} |\n"

        improvements_text = "\n".join(f"- {imp}" for imp in improvements) if improvements else "- None"

        return f"""## 6. Quality Evaluation

**Overall Grade: {grade}**

| Dimension | Score | Value |
|-----------|-------|-------|
{score_rows}

### Recommended Improvements
{improvements_text}"""

    def _metadata_section(self, result: PipelineResult) -> str:
        tokens = result.total_tokens
        stage_tokens = ""
        for name, stage in result.stages.items():
            t = stage.tokens_used
            stage_tokens += f"| {name} | {t.get('input', 0):,} | {t.get('output', 0):,} |\n"

        return f"""## 7. Pipeline Metadata

**Total Tokens:** {tokens['input'] + tokens['output']:,} (input: {tokens['input']:,}, output: {tokens['output']:,})
**Duration:** {result.duration_seconds:.1f}s

| Stage | Input Tokens | Output Tokens |
|-------|-------------|---------------|
{stage_tokens}

---

*Generated by [C.L.E.R.I.C.](https://github.com/yourusername/cleric) — Cross-Lateral Evidence Review for Information Clarity*"""

    def _slugify(self, text: str) -> str:
        slug = text.lower()[:50]
        return "".join(c if c.isalnum() else "_" for c in slug).strip("_")
