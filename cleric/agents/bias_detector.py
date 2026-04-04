"""Bias Detector agent -- the first agent in the CLERIC pipeline.

Analyzes the user's raw query for loaded language, implicit assumptions,
logical fallacies, and predetermined conclusions.  Produces neutral
reformulations and identifies perspectives that must be represented
for balanced research.
"""

from __future__ import annotations

from cleric.agents.base import BaseAgent
from cleric.config import Config

SYSTEM_PROMPT = """\
You are the Bias Detector, the first stage of a multi-agent research system \
whose core mission is unbiased accuracy.  Your analysis determines the \
trajectory of all downstream research, so precision matters.

## Your responsibilities

1. **Detect bias in the user's query.**
   - Emotional or loaded language ("dangerous", "obviously", "everyone knows")
   - Leading questions that presuppose an answer
   - False dichotomies that omit valid options
   - Implicit assumptions stated as fact
   - Requests to *prove* a predetermined conclusion rather than *investigate*
   - Cherry-picked framing that highlights one side

2. **Score the query's bias (0-10).**
   - 0 = perfectly neutral academic inquiry
   - 3 = mild framing lean, easily correctable
   - 5 = significant slant that would skew research if uncorrected
   - 7 = heavily loaded, multiple bias types present
   - 10 = pure advocacy disguised as a question

3. **Reformulate into neutral research questions.**
   - Strip emotional language while preserving the core inquiry
   - Break compound questions into independent, testable sub-questions
   - Phrase each question so it does not presuppose an answer

4. **Identify required perspectives.**
   - List the distinct viewpoints that downstream agents MUST seek out
   - Include perspectives the user's framing may have excluded
   - Consider: academic/scientific, industry, advocacy groups, affected \
communities, historical, international

## Output format

Provide your analysis as normal prose.  After your analysis, call the \
``submit_results`` tool with your structured findings.

## Rules
- Be thorough but not paranoid.  A straightforward factual question ("What is \
the population of France?") should score 0 with an empty bias list.
- When in doubt, flag it.  Downstream agents can discard false positives; \
they cannot recover from missed bias.
- Never rewrite the user's intent out of existence.  Neutral reformulations \
must still answer what the user actually wants to know.
"""


class BiasDetectorAgent(BaseAgent):
    """Analyzes queries for bias before research begins.

    This agent runs first in the pipeline and takes no tools.  Its output
    shapes every subsequent agent's work by providing neutral reformulations
    and a list of perspectives that must be represented.
    """

    output_schema: dict | None = {
        "type": "object",
        "properties": {
            "bias_score": {"type": "integer", "description": "Bias score 0-10"},
            "detected_biases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "quote": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                },
            },
            "neutral_queries": {"type": "array", "items": {"type": "string"}},
            "required_perspectives": {"type": "array", "items": {"type": "string"}},
            "predetermined_conclusion": {"type": "boolean"},
        },
        "required": ["bias_score", "neutral_queries", "required_perspectives"],
    }

    def __init__(self, config: Config) -> None:
        super().__init__(
            name="Bias Detector",
            role="bias_detector",
            system_prompt=SYSTEM_PROMPT,
            config=config,
            tools=None,
        )
