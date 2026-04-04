![CI](https://github.com/JWalts789/CLERIC/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-172%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

<div align="center">

# C.L.E.R.I.C.

**Cross-Lateral Evidence Review for Informational Clarity**

*You asked a question. You deserve the truth.*

A multi-agent AI research system that decomposes questions into specialized roles — bias detection, multi-perspective research, independent fact-checking, adversarial challenge, balanced synthesis, and quantitative evaluation — so you get auditable answers, not opinions.

[Quick Start](#quick-start) | [Web UI](#web-ui) | [Design Decisions](#design-decisions) | [Sample Output](docs/samples/)

</div>

---

## Screenshots

> **Add your own screenshots here.** Take these 3 screenshots and save them to `docs/screenshots/`:

| Landing Page | Pipeline Running | Results + Score |
|:---:|:---:|:---:|
| ![Landing](docs/screenshots/landing.png) | ![Pipeline](docs/screenshots/pipeline.png) | ![Results](docs/screenshots/results.png) |
| *Search input with query history and source reputation* | *Live pipeline progress with 6 agent stages* | *Evaluation scorecard with dimension scores* |

---

## Why This Exists

When you ask a single LLM a question, you get one perspective with no accountability. It might be right. It might be hallucinating. You have no way to tell.

| Single LLM | C.L.E.R.I.C. |
|-------------|--------|
| One perspective, one pass | Six specialized agents with distinct roles |
| No bias detection | Query analyzed and neutralized before research |
| No self-verification | Every claim independently fact-checked |
| No adversarial review | Devil's Advocate challenges all findings |
| No quality metrics | Quantitative evaluation on 6 dimensions |
| No audit trail | Full source citations, Mermaid diagrams, tool call logs |
| Answers from training data | Live web research with conflict-of-interest flagging |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/JWalts789/CLERIC.git
cd CLERIC
pip install -e .

# Add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Run a query
cleric "What are the health effects of intermittent fasting?"
```

## Web UI

The full web interface runs on Svelte 5 + FastAPI with live WebSocket streaming.

**Terminal 1 — Backend:**
```bash
cd web/backend
pip install -r requirements.txt
python run.py          # or: python run.py --demo  (loads sample results)
```

**Terminal 2 — Frontend:**
```bash
cd web/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Bring your own API key via the settings panel, or use the server's `.env` key.

---

## Architecture

```
User Query
    |
    v
[1. Bias Detector]      Strips loaded language, produces neutral queries
    |
    v
[2. Researcher]          Web search + fetch with tool-use budget (8-12 calls)
    |
    v
[3. Fact Checker]        Independent verification, searches for counter-evidence
    |
    v
[4. Devil's Advocate]    Adversarial critique — finds every weakness
    |
    v
[5. Synthesizer]         Balanced report from verified evidence only
    |
    v
[6. Evaluator]           Scores on 6 dimensions, assigns letter grade
    |
    v
Outputs: Report (.md) + Diagrams (.mermaid) + Raw Data (.json)
```

Each agent uses Claude's **tool-use protocol** for structured output — guaranteeing reliable JSON data extraction instead of hoping the model embeds it in prose.

---

## Design Decisions

### Why 6 agents instead of 1?

A single LLM answering a question is like asking one person to research, fact-check, critique, and grade their own work. They'll confirm their first instinct. C.L.E.R.I.C. separates these into roles that **check each other**:

- The Researcher gathers evidence, but the Fact Checker verifies it independently
- The Devil's Advocate attacks what everyone else agreed on
- The Synthesizer can only use verified claims
- The Evaluator scores the whole process, not just the output

This mirrors how real research institutions work — peer review, adversarial debate, editorial oversight.

### Why structured output via tool-use instead of JSON-in-prose?

Early versions asked agents to embed JSON blocks in their text responses. This worked ~70% of the time. Smaller models (Haiku) often skipped the JSON entirely, leaving downstream stages with no structured data.

The fix: each agent has a `submit_results` virtual tool with a strict JSON schema. Claude's tool-use protocol **guarantees** structured output because the model is designed to call tools reliably. The prose analysis and structured data flow through the same conversation but are captured through different channels.

This is the same architectural pattern used in production agent systems — it demonstrates understanding of the fundamental reliability problem in LLM outputs.

### Why conflict-of-interest detection?

A source's credibility depends on who produced it. Meta studying the effects of its own platform, an advocacy group funded by the industry it covers, a think tank with known political alignment — these aren't automatically wrong, but the reader needs to know about the conflict to judge for themselves.

The Researcher flags every source with a conflict level (none/low/moderate/high) and explains the stake. Sources that go **against** their own interest (like Meta's leaked internal research showing harm) are noted as potentially more credible.

### Why a source reputation system?

Individual research runs are useful. But tracking which domains consistently produce verified vs. disputed claims across **all** runs creates a community knowledge asset. Over time, C.L.E.R.I.C. learns which sources to trust — not from opinion, but from empirical verification data.

The reputation file (`data/source_reputation.json`) ships with the repo and improves with every query.

### Why BYOK (Bring Your Own Key)?

Open-source AI tools that require a server-side API key create a tension: the developer pays for usage, or the tool requires a hosted service. BYOK solves this — users bring their own Anthropic key, stored only in their browser's localStorage, sent per-request, never persisted on the server. Zero infrastructure cost, full functionality.

---

## Unbiased by Design

C.L.E.R.I.C.'s core principle: **the system actively resists bias at every stage**.

1. **Bias Detector** scores the query's bias (0-10), strips emotional language, identifies perspectives that must be represented — including ones the user's framing excluded
2. **Researcher** uses neutralized queries and actively seeks opposing viewpoints
3. **Fact Checker** searches for the *opposite* of each claim to find counter-evidence
4. **Devil's Advocate** — "If you cannot find any problems, you are not trying hard enough"
5. **Synthesizer** separates FACTS (verified), ANALYSIS (inferred), and OPINION (perspective-dependent)
6. **Evaluator** scores bias balance as one of six dimensions — favoritism gets a low score

---

## Evaluation Dimensions

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| **Source Diversity** | 15% | Were multiple perspectives represented? |
| **Claim Verification Rate** | 25% | What % of claims were independently verified? |
| **Bias Balance** | 20% | Does the output favor one side unfairly? |
| **Challenge Resolution** | 15% | Were the Devil's Advocate challenges addressed? |
| **Source Quality** | 15% | Are sources credible and varied? |
| **Internal Consistency** | 10% | Do the findings contradict themselves? |

Grade scale: A (0.85+) through F (0.00-0.29). The evaluator is calibrated to score harshly — 0.8+ is genuinely impressive.

---

## Features

- **6-agent pipeline** with structured output (Claude tool-use protocol)
- **Live web UI** — Svelte 5 + FastAPI + WebSocket streaming
- **Bias detection** with neutral query reformulation
- **Conflict-of-interest flagging** on all sources
- **Source reputation tracking** — domain credibility scores across runs
- **Query history** — SQLite persistence with search
- **Export** — Markdown, JSON, and Print-to-PDF
- **Settings panel** — model selection (Haiku/Sonnet/Opus) with cost estimates
- **BYOK** — bring your own Anthropic API key
- **Demo mode** — browse sample results without an API key
- **6 Mermaid diagrams** per research run
- **172 tests, 93% coverage**, CI/CD pipeline
- **Accessibility** — ARIA labels, keyboard navigation, reduced-motion support

---

## Sample Output

See [docs/samples/](docs/samples/) for complete research outputs you can browse without running the tool.

**Example: "Is social media harmful to teenagers' mental health?"**
- Bias Score: 3/10 (mild binary framing detected)
- 16 sources across multiple perspectives
- 5 claims fact-checked (2 verified, 2 disputed, 1 unverified)
- 10 adversarial challenges raised
- Grade: C+ (evaluator flagged source diversity and verification gaps)
- [Full report](docs/samples/social_media_mental_health/report.md) | [Raw data](docs/samples/social_media_mental_health/raw_data.json)

---

## CLI Usage

```bash
cleric "Your research question"              # Basic query
cleric "Is nuclear energy safe?" --json       # JSON output
cleric "..." --verbose                        # Show all agent outputs
cleric "..." --model claude-sonnet-4-6        # Specific model
cleric "..." --no-mermaid --no-report         # Skip file generation
```

### Python API

```python
from cleric.config import Config
from cleric.orchestrator import ResearchPipeline

config = Config.from_env()
pipeline = ResearchPipeline(config)
result = pipeline.run("What are the economic effects of universal basic income?")

print(f"Grade: {result.overall_grade}")
print(f"Bias Score: {result.stages['bias_detection'].data.get('bias_score')}")
```

---

## Project Structure

```
cleric/
  agents/              # 6 specialized agents + base class
  tools/               # Web search, page fetch, file I/O, tool registry
  memory/              # Persistent JSON memory store
  output/              # Mermaid diagram + Markdown report generators
  reputation.py        # Community source credibility tracking
  orchestrator.py      # Pipeline that chains all agents
  cli.py               # Rich terminal interface
  config.py            # Environment-based configuration
web/
  backend/             # FastAPI + WebSocket server, SQLite store
  frontend/            # Svelte 5 + TypeScript UI
tests/                 # 172 tests, 93% coverage
docs/
  samples/             # Curated research output samples
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `CLERIC_MODEL` | `claude-sonnet-4-6` | Claude model |
| `CLERIC_MAX_SEARCH_RESULTS` | `10` | Max results per search |
| `CLERIC_MAX_TOKENS` | `4096` | Max tokens per agent call |

## Running Tests

```bash
pytest tests/ -v --cov=cleric    # 172 tests, 93% coverage
```

## License

MIT

---

<div align="center">

**Built by [JWalts789](https://github.com/JWalts789)** | Powered by [Claude](https://anthropic.com) | [View Sample Output](docs/samples/)

</div>
