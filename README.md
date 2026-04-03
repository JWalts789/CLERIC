# C.L.E.R.I.C.

**Cross-Lateral Evidence Review for Information Clarity**

C.L.E.R.I.C. decomposes research into specialized agent roles that check each other's work. Instead of trusting a single LLM response, it runs a six-stage pipeline: bias detection, multi-perspective research, independent fact-checking, adversarial challenge, balanced synthesis, and quantitative evaluation.

Every claim is sourced. Every bias is flagged. Every weakness is challenged. The result is research you can audit.

## Architecture

```
User Query
    |
    v
+-------------------+
| 1. Bias Detector  |  Analyzes query for loaded language, assumptions,
|    (no tools)     |  and predetermined conclusions. Produces neutral
|                   |  reformulations and required perspectives.
+-------------------+
    |
    v
+-------------------+
| 2. Researcher     |  Searches the web using neutral queries. Actively
|    (web tools)    |  seeks opposing viewpoints. Gathers sources that
|                   |  disagree with each other.
+-------------------+
    |
    v
+-------------------+
| 3. Fact Checker   |  Independently verifies EACH claim from the
|    (web tools)    |  Researcher. Searches for counter-evidence.
|                   |  Categories: VERIFIED / DISPUTED / UNVERIFIED / FALSE
+-------------------+
    |
    v
+-------------------+
| 4. Devil's        |  Argues AGAINST the emerging consensus. Identifies
|    Advocate       |  weak evidence, logical gaps, missing perspectives,
|    (no tools)     |  and cherry-picking.
+-------------------+
    |
    v
+-------------------+
| 5. Synthesizer    |  Produces the final report using ONLY verified
|    (no tools)     |  claims. Presents multiple viewpoints. Addresses
|                   |  every challenge from the Devil's Advocate.
+-------------------+
    |
    v
+-------------------+
| 6. Evaluator      |  Scores the research on 6 dimensions (0.0-1.0).
|    (no tools)     |  Assigns a letter grade. Identifies specific
|                   |  areas for improvement.
+-------------------+
    |
    v
Outputs: Report (.md) + Diagrams (.mermaid) + Raw Data (.json)
```

## Why Not Just Ask an LLM?

| Single LLM | C.L.E.R.I.C. |
|-------------|--------|
| One perspective, one pass | Six specialized agents with distinct roles |
| No bias detection | Query analyzed for bias before research begins |
| No self-verification | Every claim independently fact-checked |
| No adversarial review | Devil's Advocate challenges all findings |
| No quality metrics | Quantitative evaluation on 6 dimensions |
| No audit trail | Full tool call logs, source citations, Mermaid diagrams |
| Answers from training data | Answers from live web research with sources |

## Installation

```bash
git clone https://github.com/yourusername/cleric.git
cd cleric
pip install -e .
```

Copy the environment template and add your API key:

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

## Usage

```bash
# Basic research query
cleric "What are the health effects of intermittent fasting?"

# With JSON output
cleric "Is nuclear energy safe?" --json

# Skip diagram generation
cleric "What caused the 2008 financial crisis?" --no-mermaid

# Verbose mode (show all agent outputs)
cleric "Are electric vehicles better for the environment?" --verbose

# Use a specific model
cleric "What is quantum computing?" --model claude-sonnet-4-6
```

### Python API

```python
from cleric.config import Config
from cleric.orchestrator import ResearchPipeline
from cleric.output.mermaid import MermaidGenerator
from cleric.output.report import ReportGenerator

config = Config.from_env()
pipeline = ResearchPipeline(config)

result = pipeline.run("What are the economic effects of universal basic income?")

# Access structured data
print(f"Grade: {result.overall_grade}")
print(f"Bias Score: {result.stages['bias_detection'].data.get('bias_score')}")
print(f"Duration: {result.duration_seconds:.1f}s")

# Generate outputs
mermaid = MermaidGenerator(config.output_dir)
diagrams = mermaid.generate_all(result)

reporter = ReportGenerator(config.output_dir)
report_path = reporter.generate(result)
```

## Unbiased by Design

C.L.E.R.I.C.'s core principle is that **the system actively resists bias at every stage**:

1. **Bias Detector** runs before any research. It scores the query's bias (0-10), strips loaded language, and identifies perspectives that must be represented — including perspectives the user's framing may have excluded.

2. **Researcher** uses the neutralized queries, not the original. It's instructed to seek disagreement, not confirmation.

3. **Fact Checker** operates independently from the Researcher. For each claim, it searches for the *opposite* assertion to see if counter-evidence exists.

4. **Devil's Advocate** exists solely to challenge the emerging consensus. Its system prompt says: "If you cannot find any problems, you are not trying hard enough."

5. **Synthesizer** separates FACTS (verified), ANALYSIS (inferred), and OPINION (perspective-dependent). It must address every challenge raised by the Devil's Advocate.

6. **Evaluator** scores bias balance as one of six dimensions. A report that favors one side unfairly gets a low score.

## Output Formats

### Mermaid Diagrams

Every research run generates six Mermaid diagrams:

| Diagram | Shows |
|---------|-------|
| `pipeline_flow` | Full agent chain with metrics |
| `bias_analysis` | Detected biases, neutral reformulations, required perspectives |
| `source_map` | Sources organized by perspective |
| `verification_status` | Fact-check results for each claim |
| `evaluation_scorecard` | Scores on 6 dimensions with visual bars |
| `agent_interaction` | Sequence diagram of agent communication |

### Markdown Report

A comprehensive research report with sections for each pipeline stage, including source citations, verification status, challenges addressed, and evaluation scores.

### Raw JSON

Complete structured data from all agents, including tool call logs and token usage.

## Evaluation Dimensions

The Evaluator scores research on six dimensions (each 0.0-1.0):

| Dimension | What it measures |
|-----------|-----------------|
| **Source Diversity** | Were multiple perspectives represented? |
| **Claim Verification Rate** | What % of claims were independently verified? |
| **Bias Balance** | Does the output favor one side unfairly? |
| **Challenge Resolution** | Were the Devil's Advocate challenges addressed? |
| **Source Quality** | Are sources credible and varied? |
| **Internal Consistency** | Do the findings contradict themselves? |

Overall grade: weighted average mapped to A-F scale. A score of 0.8+ is genuinely impressive research.

## Memory System

CLERIC maintains a persistent JSON-based memory store. When you research a topic, key findings are stored with confidence scores. Future research on related topics can build on prior work instead of starting from scratch.

```
memory_store/
  quantum_computing.json    # Findings from prior research
  climate_policy.json       # Each topic gets its own file
```

## Project Structure

```
cleric/
  __init__.py
  config.py              # Environment-based configuration
  cli.py                 # Rich terminal interface
  orchestrator.py        # Pipeline that chains all agents
  agents/
    __init__.py
    base.py              # BaseAgent with tool-use loop
    bias_detector.py     # Stage 1: Query bias analysis
    researcher.py        # Stage 2: Multi-perspective research
    fact_checker.py      # Stage 3: Independent verification
    devils_advocate.py   # Stage 4: Adversarial challenge
    synthesizer.py       # Stage 5: Balanced synthesis
    evaluator.py         # Stage 6: Quantitative scoring
  tools/
    __init__.py
    registry.py          # Tool registry for Claude API
    web_search.py        # DuckDuckGo search
    web_fetch.py         # Page fetch + text extraction
    file_io.py           # File read/write
  memory/
    __init__.py
    store.py             # Persistent JSON memory store
  output/
    __init__.py
    mermaid.py           # Mermaid diagram generator
    report.py            # Markdown report generator
tests/
  test_config.py
  test_tools.py
  test_memory.py
  test_agents.py
  test_orchestrator.py
  test_mermaid.py
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `CLERIC_MODEL` | `claude-sonnet-4-6` | Claude model to use |
| `CLERIC_MAX_SEARCH_RESULTS` | `10` | Max results per web search |
| `CLERIC_MEMORY_DIR` | `./memory_store` | Memory persistence directory |
| `CLERIC_OUTPUT_DIR` | `./output` | Output file directory |
| `CLERIC_MAX_TOKENS` | `4096` | Max tokens per agent call |

## Running Tests

```bash
pytest tests/ -v --cov=cleric
```

## License

MIT
