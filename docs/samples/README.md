# Sample Outputs

These are real outputs from C.L.E.R.I.C. research runs, included so you can evaluate the system's output quality without needing an API key.

## Sample 1: Social Media and Teenage Mental Health

**Query:** "Is social media harmful to teenagers' mental health?"
**Model:** Claude Haiku 4.5
**Grade:** C+
**Duration:** 326 seconds
**Cost:** ~$0.20

A deliberately controversial topic with strong opinions on both sides. The system:
- Detected binary framing bias (score 3/10) and reformulated into 3 neutral research questions
- Gathered 16 sources across multiple perspectives
- Fact-checked 5 key claims (2 verified, 2 disputed, 1 unverified)
- Devil's Advocate raised 10 challenges including correlation-causation conflation and publication bias
- Synthesized a balanced report separating facts, analysis, and opinion
- Evaluator scored harshly on source diversity and verification rate

### Files

| File | Description |
|------|-------------|
| [report.md](social_media_mental_health/report.md) | Full research report (46KB) |
| [raw_data.json](social_media_mental_health/raw_data.json) | Complete structured data from all agents |
| [pipeline_flow.mermaid](social_media_mental_health/pipeline_flow.mermaid) | Pipeline architecture diagram |
| [bias_analysis.mermaid](social_media_mental_health/bias_analysis.mermaid) | Bias detection breakdown |
| [source_map.mermaid](social_media_mental_health/source_map.mermaid) | Sources organized by perspective |
| [verification_status.mermaid](social_media_mental_health/verification_status.mermaid) | Fact-check results |
| [evaluation_scorecard.mermaid](social_media_mental_health/evaluation_scorecard.mermaid) | Quality scores on 6 dimensions |
| [agent_interaction.mermaid](social_media_mental_health/agent_interaction.mermaid) | Agent communication sequence |

### Viewing Mermaid Diagrams

Paste any `.mermaid` file's contents into [mermaid.live](https://mermaid.live) to render it as a visual diagram.
