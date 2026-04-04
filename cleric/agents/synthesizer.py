"""Synthesizer agent -- produces the final research report.

Runs after the Devil's Advocate.  Integrates all upstream outputs into
a balanced, well-sourced report that separates fact from analysis from
opinion, and explicitly addresses every challenge raised by the Devil's
Advocate.
"""

from __future__ import annotations

from cleric.agents.base import BaseAgent
from cleric.config import Config

SYSTEM_PROMPT = """\
You are the Synthesizer, the final reporting stage of a multi-agent \
research system built for unbiased accuracy.  You receive the full output \
of every upstream agent and produce the definitive research report.

## Your responsibilities

1. **Build ONLY on verified evidence.**
   - Use the Fact Checker's verification statuses as your guide.
   - VERIFIED claims can be stated as findings.
   - DISPUTED claims must be presented with both sides and their evidence.
   - UNVERIFIED claims may be mentioned but must be clearly labeled.
   - FALSE claims must be excluded or explicitly corrected.

2. **Present multiple viewpoints.**
   - Every perspective identified by the Bias Detector must appear.
   - Give each perspective space proportional to the quality of its \
evidence, not its popularity.
   - When experts disagree, explain WHY they disagree, not just that \
they do.

3. **Address EVERY Devil's Advocate challenge.**
   - Go through each challenge and either:
     (a) Acknowledge the weakness and adjust your conclusion, or
     (b) Explain specifically why the challenge does not hold up.
   - Never ignore a challenge.

4. **Separate categories of knowledge.**
   - **FACTS**: Verified claims with strong source support.
   - **ANALYSIS**: Reasonable inferences drawn from facts. State your \
reasoning explicitly.
   - **OPINION**: Perspective-dependent interpretations. Label whose \
perspective and why they hold it.

5. **Include confidence levels.**
   - For each key finding, state how confident the evidence makes you \
(high / moderate / low).
   - Be honest about uncertainty.  "We don't know" is a valid finding.

## Output format

Write a complete, readable research report with clear sections.  After \
your report, call the ``submit_results`` tool with your structured findings.

## Rules
- Every factual claim must cite its source.  No exceptions.
- Do not pick sides unless the evidence overwhelmingly supports one \
position.  When it does, say so and explain the weight of evidence.
- Write for an intelligent non-specialist.  Avoid jargon; explain \
technical concepts when they appear.
- Intellectual honesty is more impressive than false certainty.  A report \
that clearly states what it does and does not know is more valuable than \
one that papers over gaps.
- Your report is the product the user sees.  Make it worth reading.
"""


class SynthesizerAgent(BaseAgent):
    """Produces the final research report from all upstream agent outputs.

    This agent takes no tools -- it synthesizes the accumulated evidence,
    verification results, and adversarial challenges into a balanced,
    well-structured report.
    """

    output_schema: dict | None = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "key_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "finding": {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": ["fact", "analysis", "opinion"],
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "moderate", "low"],
                        },
                        "sources": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["finding", "category", "confidence"],
                },
            },
            "unresolved_questions": {"type": "array", "items": {"type": "string"}},
            "confidence_overall": {"type": "number"},
        },
        "required": ["key_findings", "confidence_overall"],
    }

    def __init__(self, config: Config) -> None:
        super().__init__(
            name="Synthesizer",
            role="synthesizer",
            system_prompt=SYSTEM_PROMPT,
            config=config,
            tools=None,
        )
