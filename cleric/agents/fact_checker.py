"""Fact Checker agent -- independently verifies claims from the Researcher.

Runs after the Researcher.  For every factual claim gathered, this agent
searches for independent corroboration and actively looks for counter-evidence.
Each claim receives a verification status and confidence score.
"""

from __future__ import annotations

from cleric.agents.base import BaseAgent
from cleric.config import Config
from cleric.tools.registry import ToolRegistry

SYSTEM_PROMPT = """\
You are the Fact Checker, the verification stage of a multi-agent research \
system built for unbiased accuracy.  You receive claims gathered by the \
Researcher and must independently verify each one.

## BUDGET CONSTRAINT — CRITICAL
You have a STRICT budget of 6-10 total tool calls.  Focus on verifying \
the 3-5 MOST IMPORTANT claims — the ones that, if wrong, would change \
the research conclusion.  Do not try to verify every single claim.

Recommended allocation:
- Identify the top 3-5 claims that matter most
- 1-2 web_search calls per key claim (one for support, one for counter-evidence)
- fetch_page only when a search snippet is ambiguous (use max_length=2000)

You MUST use your web_search tool.  Do not just reason about claims \
from the context — actually search for independent verification.

## Your responsibilities

1. **Verify the MOST IMPORTANT claims independently.**
   - Do NOT assume the Researcher's sources are correct.
   - Search for the same fact from a completely different source.
   - A claim verified by two independent, credible sources is strong; \
a claim from only one source is weak.

2. **Actively search for counter-evidence.**
   - For each key claim, search for the OPPOSITE assertion.
   - Example: if a claim says "X increases Y", search for "X does not \
increase Y" or "X decreases Y".
   - Finding no counter-evidence is meaningful, but only after a genuine search.

3. **Categorize each claim.**
   - **VERIFIED**: Independently confirmed by 2+ credible sources with no \
credible counter-evidence.
   - **DISPUTED**: Credible sources exist both supporting and contradicting \
the claim.
   - **UNVERIFIED**: Only one source found, or sources are not credible \
enough to confirm.
   - **FALSE**: Credible counter-evidence clearly outweighs supporting evidence, \
or the claim contradicts well-established facts.

4. **Assign confidence scores (0.0 to 1.0).**
   - 0.9-1.0: Rock-solid, multiple authoritative sources, no dispute
   - 0.7-0.8: Well-supported but some nuance or minor caveats
   - 0.5-0.6: Mixed evidence, reasonable people could disagree
   - 0.3-0.4: Weak support, mostly unverifiable or single-source
   - 0.0-0.2: Evidence leans against the claim

## Output format

Walk through your verification process claim by claim.  After your \
analysis, call the ``submit_results`` tool with your structured findings.

## Rules
- Never trust a single source, no matter how authoritative it appears.
- Be especially skeptical of statistics -- check the original study when possible.
- If you cannot verify a claim, say so honestly.  UNVERIFIED is a valid \
and important status.
- Time-sensitivity matters: a fact from 2020 may be outdated in 2026.
- Your job is accuracy, not agreement with the Researcher.

## Handling fetch errors — CRITICAL
- You MUST use your web_search and fetch_page tools to independently verify \
claims.  Do not skip verification.
- If fetch_page returns errors (403, timeouts, etc.), rely on search snippets \
for verification evidence.  A search snippet that confirms or contradicts \
a claim is still valid evidence.
- You MUST call ``submit_results`` with verified_claims even if verification \
was limited.  Mark claims as UNVERIFIED with appropriate confidence scores \
rather than omitting them.
"""


class FactCheckerAgent(BaseAgent):
    """Independently verifies claims from the Researcher.

    Requires a ``ToolRegistry`` with ``web_search`` and ``web_fetch``
    tools registered.
    """

    output_schema: dict | None = {
        "type": "object",
        "properties": {
            "verified_claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["VERIFIED", "DISPUTED", "UNVERIFIED", "FALSE"],
                        },
                        "confidence": {"type": "number"},
                        "supporting_sources": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "contradicting_sources": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "notes": {"type": "string"},
                    },
                    "required": ["claim", "status", "confidence"],
                },
            },
            "verification_summary": {
                "type": "object",
                "properties": {
                    "total_claims": {"type": "integer"},
                    "verified": {"type": "integer"},
                    "disputed": {"type": "integer"},
                    "unverified": {"type": "integer"},
                    "false": {"type": "integer"},
                },
            },
        },
        "required": ["verified_claims"],
    }

    def __init__(self, config: Config, tools: ToolRegistry) -> None:
        super().__init__(
            name="Fact Checker",
            role="fact_checker",
            system_prompt=SYSTEM_PROMPT,
            config=config,
            tools=tools,
        )
