"""Mermaid diagram generator for research pipeline visualization.

Produces .mermaid files that document the full research process:
- Pipeline flow diagram showing agent chain
- Bias analysis breakdown
- Source relationship map
- Fact-check verification status
- Evaluation scorecard
"""

from pathlib import Path
from datetime import datetime, timezone

from cleric.orchestrator import PipelineResult


class MermaidGenerator:
    """Generates Mermaid diagram files from pipeline results."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, result: PipelineResult) -> dict[str, Path]:
        """Generate all diagrams for a pipeline result. Returns {name: filepath}."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = self._slugify(result.query)
        prefix = f"{timestamp}_{slug}"

        files = {}
        files["pipeline_flow"] = self._write(
            f"{prefix}_pipeline_flow.mermaid",
            self._pipeline_flow(result),
        )
        files["bias_analysis"] = self._write(
            f"{prefix}_bias_analysis.mermaid",
            self._bias_analysis(result),
        )
        files["source_map"] = self._write(
            f"{prefix}_source_map.mermaid",
            self._source_map(result),
        )
        files["verification_status"] = self._write(
            f"{prefix}_verification_status.mermaid",
            self._verification_status(result),
        )
        files["evaluation_scorecard"] = self._write(
            f"{prefix}_evaluation_scorecard.mermaid",
            self._evaluation_scorecard(result),
        )
        files["agent_interaction"] = self._write(
            f"{prefix}_agent_interaction.mermaid",
            self._agent_interaction(result),
        )
        return files

    def _write(self, filename: str, content: str) -> Path:
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def _slugify(self, text: str) -> str:
        slug = text.lower()[:50]
        return "".join(c if c.isalnum() else "_" for c in slug).strip("_")

    def _pipeline_flow(self, result: PipelineResult) -> str:
        """Main pipeline flow diagram showing the agent chain and data flow."""
        stages = result.stages
        tokens = result.total_tokens

        bias_score = stages.get("bias_detection", None)
        bias_val = bias_score.data.get("bias_score", "?") if bias_score else "?"

        eval_stage = stages.get("evaluation", None)
        grade = eval_stage.data.get("grade", "?") if eval_stage else "?"
        overall = eval_stage.data.get("scores", {}).get("overall_score", "?") if eval_stage else "?"

        return f"""---
title: "C.L.E.R.I.C. Research Pipeline"
---
%%{{init: {{"theme": "base", "themeVariables": {{"primaryColor": "#2d3748", "primaryTextColor": "#fff", "primaryBorderColor": "#4a5568", "lineColor": "#718096", "secondaryColor": "#4a5568", "tertiaryColor": "#2d3748"}}}}}}%%
flowchart TD
    Q["🔍 User Query<br/><i>{self._escape(result.query[:80])}</i>"]

    subgraph PIPELINE["Research Pipeline"]
        direction TB
        BD["🛡️ Bias Detector<br/>Bias Score: {bias_val}/10"]
        R["🔎 Researcher<br/>Web Search + Fetch"]
        FC["✅ Fact Checker<br/>Independent Verification"]
        DA["😈 Devil's Advocate<br/>Adversarial Challenge"]
        S["📝 Synthesizer<br/>Balanced Report"]
        E["📊 Evaluator<br/>Grade: {grade} ({overall})"]
    end

    Q --> BD
    BD -->|"Neutral queries<br/>+ required perspectives"| R
    R -->|"Sources + claims"| FC
    FC -->|"Verified claims"| DA
    DA -->|"Challenges"| S
    S -->|"Final report"| E

    subgraph TOOLS["Tool Layer"]
        WS["🌐 Web Search"]
        WF["📄 Web Fetch"]
    end

    R -.->|uses| WS
    R -.->|uses| WF
    FC -.->|uses| WS
    FC -.->|uses| WF

    subgraph MEMORY["Memory Layer"]
        MS["💾 Persistent Store<br/>Prior Research Context"]
    end

    Q -.->|"check prior research"| MS
    E -.->|"store findings"| MS

    subgraph METRICS["Run Metrics"]
        TK["Tokens: {tokens['input'] + tokens['output']:,} total"]
        DUR["Duration: {result.duration_seconds:.1f}s"]
    end

    style BD fill:#e53e3e,color:#fff
    style R fill:#3182ce,color:#fff
    style FC fill:#38a169,color:#fff
    style DA fill:#d69e2e,color:#fff
    style S fill:#805ad5,color:#fff
    style E fill:#dd6b20,color:#fff
"""

    def _bias_analysis(self, result: PipelineResult) -> str:
        """Diagram showing detected biases and neutral reformulations."""
        bias_stage = result.stages.get("bias_detection")
        if not bias_stage:
            return self._empty_diagram("No bias analysis data")

        data = bias_stage.data
        bias_score = data.get("bias_score", 0)
        detected = data.get("detected_biases", [])
        neutral = data.get("neutral_queries", [])
        perspectives = data.get("required_perspectives", [])

        # Build bias nodes
        bias_nodes = ""
        for i, bias in enumerate(detected[:6]):
            if isinstance(bias, dict):
                bias_type = self._escape(str(bias.get("type", ""))[:30])
                quote = self._escape(str(bias.get("quote", ""))[:30])
                label = f"{bias_type}<br/><small>'{quote}'</small>"
            else:
                label = self._escape(str(bias)[:60])
            bias_nodes += f'        B{i}["{label}"]\n'

        # Build neutral query nodes
        neutral_nodes = ""
        for i, nq in enumerate(neutral[:4]):
            label = self._escape(str(nq)[:80])
            neutral_nodes += f'        NQ{i}["{label}"]\n'

        # Build perspective nodes
        perspective_nodes = ""
        for i, p in enumerate(perspectives[:6]):
            label = self._escape(str(p)[:50])
            perspective_nodes += f'        P{i}["{label}"]\n'

        # Color based on bias score
        if bias_score <= 3:
            color = "#38a169"
            label = "Low Bias"
        elif bias_score <= 6:
            color = "#d69e2e"
            label = "Moderate Bias"
        else:
            color = "#e53e3e"
            label = "High Bias"

        return f"""---
title: "Bias Analysis — Score: {bias_score}/10 ({label})"
---
flowchart TD
    OQ["Original Query<br/><i>{self._escape(result.query[:80])}</i>"]

    subgraph BIASES["Detected Biases"]
{bias_nodes}    end

    subgraph NEUTRAL["Neutral Reformulations"]
{neutral_nodes}    end

    subgraph PERSPECTIVES["Required Perspectives"]
{perspective_nodes}    end

    OQ --> BIASES
    BIASES --> NEUTRAL
    NEUTRAL --> PERSPECTIVES

    style OQ fill:{color},color:#fff
"""

    def _source_map(self, result: PipelineResult) -> str:
        """Diagram mapping sources and their relationships."""
        research_stage = result.stages.get("research")
        if not research_stage:
            return self._empty_diagram("No research data")

        sources = research_stage.data.get("sources", [])
        if not sources:
            return self._empty_diagram("No sources found in research data")

        conflict_icons = {
            "high": "🔴",
            "moderate": "🟡",
            "low": "🟢",
            "none": "⚪",
        }
        conflict_colors = {
            "high": "#e53e3e",
            "moderate": "#d69e2e",
            "low": "#38a169",
            "none": "#718096",
        }

        source_nodes = ""
        source_styles = ""
        perspective_groups: dict[str, list[int]] = {}
        conflict_counts: dict[str, int] = {"high": 0, "moderate": 0, "low": 0, "none": 0}

        for i, source in enumerate(sources[:12]):
            title = self._escape(str(source.get("title", f"Source {i}"))[:50])
            url = self._escape(str(source.get("url", ""))[:40])
            perspective = str(source.get("perspective", "neutral"))
            conflict = str(source.get("conflict_of_interest", "none")).lower()
            conflict_detail = self._escape(str(source.get("conflict_detail", ""))[:60])
            icon = conflict_icons.get(conflict, "⚪")

            conflict_counts[conflict] = conflict_counts.get(conflict, 0) + 1

            # Build node label with conflict indicator
            label = f"{icon} {title}<br/><small>{url}</small>"
            if conflict in ("high", "moderate") and conflict_detail:
                label += f"<br/><small><i>COI: {conflict_detail}</i></small>"

            source_nodes += f'    S{i}["{label}"]\n'

            # Style high-conflict sources with a warning border
            if conflict == "high":
                source_styles += f"    style S{i} stroke:#e53e3e,stroke-width:3px,stroke-dasharray:5 5\n"
            elif conflict == "moderate":
                source_styles += f"    style S{i} stroke:#d69e2e,stroke-width:2px,stroke-dasharray:5 5\n"

            if perspective not in perspective_groups:
                perspective_groups[perspective] = []
            perspective_groups[perspective].append(i)

        # Build subgraphs by perspective
        subgraphs = ""
        colors = ["#3182ce", "#e53e3e", "#38a169", "#d69e2e", "#805ad5", "#dd6b20"]
        for idx, (perspective, indices) in enumerate(perspective_groups.items()):
            color = colors[idx % len(colors)]
            label = self._escape(perspective[:30])
            nodes = "\n".join(f"        S{i}" for i in indices)
            subgraphs += f"""
    subgraph PG{idx}["{label}"]
{nodes}
    end
    style PG{idx} fill:{color},color:#fff,stroke:{color}
"""

        # Build conflict legend
        conflict_summary = " | ".join(
            f"{conflict_icons[k]} {k.title()}: {v}"
            for k, v in conflict_counts.items() if v > 0
        )

        return f"""---
title: "Source Map — {len(sources)} Sources | Conflicts: {conflict_summary}"
---
flowchart LR
    Q["Research Query"]
    LEGEND["Conflict of Interest Legend<br/>{conflict_summary}"]

{source_nodes}
{source_styles}
{subgraphs}
    Q --> PG0
"""

    def _verification_status(self, result: PipelineResult) -> str:
        """Diagram showing fact-check verification status of claims."""
        fc_stage = result.stages.get("fact_checking")
        if not fc_stage:
            return self._empty_diagram("No fact-checking data")

        claims = fc_stage.data.get("verified_claims", fc_stage.data.get("claims", []))
        if not claims:
            return self._empty_diagram("No claims found in fact-check data")

        status_icons = {
            "VERIFIED": "✅",
            "DISPUTED": "⚠️",
            "UNVERIFIED": "❓",
            "FALSE": "❌",
        }
        status_colors = {
            "VERIFIED": "#38a169",
            "DISPUTED": "#d69e2e",
            "UNVERIFIED": "#718096",
            "FALSE": "#e53e3e",
        }

        claim_nodes = ""
        for i, claim in enumerate(claims[:15]):
            text = self._escape(str(claim.get("claim", ""))[:60])
            status = str(claim.get("status", "UNVERIFIED")).upper()
            confidence = claim.get("confidence", 0)
            icon = status_icons.get(status, "❓")
            color = status_colors.get(status, "#718096")
            claim_nodes += f'    C{i}["{icon} {text}<br/>Confidence: {confidence:.0%}"]\n'
            claim_nodes += f"    style C{i} fill:{color},color:#fff\n"

        # Summary counts
        counts = {}
        for claim in claims:
            s = str(claim.get("status", "UNVERIFIED")).upper()
            counts[s] = counts.get(s, 0) + 1

        summary_parts = [f"{status_icons.get(k, '?')} {k}: {v}" for k, v in counts.items()]
        summary = " | ".join(summary_parts)

        return f"""---
title: "Fact Verification Status — {summary}"
---
flowchart TD
    HEADER["Claim Verification Results<br/>{summary}"]

{claim_nodes}
"""

    def _evaluation_scorecard(self, result: PipelineResult) -> str:
        """Scorecard diagram showing evaluation metrics."""
        eval_stage = result.stages.get("evaluation")
        if not eval_stage:
            return self._empty_diagram("No evaluation data")

        scores = eval_stage.data.get("scores", {})
        grade = eval_stage.data.get("grade", "?")
        improvements = eval_stage.data.get("improvements", [])

        # Build score bars
        score_rows = ""
        for metric, score in scores.items():
            if isinstance(score, (int, float)):
                node_id = metric.upper()
                label = metric.replace("_", " ").title()
                bar_fill = int(score * 10)
                bar = "█" * bar_fill + "░" * (10 - bar_fill)
                score_rows += f'    {node_id}["{label}<br/>{bar} {score:.0%}"]\n'
                if score >= 0.8:
                    score_rows += f"    style {node_id} fill:#38a169,color:#fff\n"
                elif score >= 0.6:
                    score_rows += f"    style {node_id} fill:#d69e2e,color:#fff\n"
                else:
                    score_rows += f"    style {node_id} fill:#e53e3e,color:#fff\n"

        improvement_nodes = ""
        for i, imp in enumerate(improvements[:5]):
            if isinstance(imp, dict):
                area = imp.get("area", "").replace("_", " ").title()
                issue = self._escape(str(imp.get("issue", ""))[:60])
                label = f"{area}: {issue}"
            else:
                label = self._escape(str(imp)[:70])
            improvement_nodes += f'    I{i}["{label}"]\n'

        overall = eval_stage.data.get("overall_score", scores.get("overall_score", 0))

        return f"""---
title: "Research Quality Evaluation — Grade: {grade} ({overall:.0%})"
---
flowchart TD
    GRADE["Overall Grade: {grade}<br/>Score: {overall:.0%}"]

    subgraph SCORES["Dimension Scores"]
{score_rows}    end

    subgraph IMPROVEMENTS["Recommended Improvements"]
{improvement_nodes}    end

    GRADE --> SCORES
    SCORES --> IMPROVEMENTS
"""

    def _agent_interaction(self, result: PipelineResult) -> str:
        """Sequence diagram showing agent interactions and data flow."""
        stages = result.stages

        # Build tool call annotations
        research_tools = len(stages.get("research", _EMPTY_RESULT).tool_calls_made)
        fc_tools = len(stages.get("fact_checking", _EMPTY_RESULT).tool_calls_made)

        return f"""---
title: "Agent Interaction Sequence"
---
sequenceDiagram
    participant U as User
    participant BD as Bias Detector
    participant R as Researcher
    participant FC as Fact Checker
    participant DA as Devil's Advocate
    participant S as Synthesizer
    participant E as Evaluator
    participant T as Tools
    participant M as Memory

    U->>BD: Submit query
    Note over BD: Analyze for bias,<br/>reformulate neutrally

    BD->>R: Neutral queries +<br/>required perspectives
    R->>T: Web searches ({research_tools} calls)
    T-->>R: Search results + page content
    Note over R: Gather multi-perspective<br/>sources

    R->>FC: Sources + claims
    FC->>T: Verification searches ({fc_tools} calls)
    T-->>FC: Independent sources
    Note over FC: Verify each claim<br/>independently

    FC->>DA: Verified claims
    Note over DA: Challenge findings,<br/>find weaknesses

    DA->>S: Challenges + findings
    Note over S: Synthesize balanced<br/>report from verified data

    S->>E: Final report + all data
    Note over E: Score on 6 dimensions,<br/>assign grade

    E->>M: Store key findings
    E->>U: Report + evaluation +<br/>Mermaid diagrams
"""

    def _empty_diagram(self, reason: str) -> str:
        return f"""---
title: "{reason}"
---
flowchart TD
    A["{reason}"]
"""

    def _escape(self, text: str) -> str:
        """Escape characters that break Mermaid syntax."""
        return (
            text.replace("&", "&amp;")
            .replace('"', "'")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("#", "&num;")
            .replace("(", "&lpar;")
            .replace(")", "&rpar;")
            .replace("[", "&lbrack;")
            .replace("]", "&rbrack;")
            .replace("{", "&lbrace;")
            .replace("}", "&rbrace;")
            .replace("|", "&vert;")
            .replace("\n", " ")
        )


class _EmptyResult:
    """Placeholder for missing stage results."""
    tool_calls_made: list = []
    data: dict = {}
    content: str = ""

_EMPTY_RESULT = _EmptyResult()
