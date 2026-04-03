"""Pipeline orchestrator that chains agents in sequence for unbiased research."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cleric.agents.base import AgentResult
from cleric.agents.bias_detector import BiasDetectorAgent
from cleric.agents.researcher import ResearcherAgent
from cleric.agents.fact_checker import FactCheckerAgent
from cleric.agents.devils_advocate import DevilsAdvocateAgent
from cleric.agents.synthesizer import SynthesizerAgent
from cleric.agents.evaluator import EvaluatorAgent
from cleric.config import Config
from cleric.memory.store import MemoryStore
from cleric.tools.registry import create_default_registry


@dataclass
class PipelineResult:
    """Complete result from a full research pipeline run."""

    query: str
    timestamp: str
    stages: dict[str, AgentResult] = field(default_factory=dict)
    final_report: str = ""
    evaluation_scores: dict = field(default_factory=dict)
    overall_grade: str = ""
    total_tokens: dict = field(default_factory=lambda: {"input": 0, "output": 0})
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Serialize for JSON output."""
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "stages": {
                name: {
                    "agent": result.agent_name,
                    "role": result.role,
                    "data": result.data,
                    "tool_calls": result.tool_calls_made,
                    "tokens": result.tokens_used,
                }
                for name, result in self.stages.items()
            },
            "evaluation": self.evaluation_scores,
            "overall_grade": self.overall_grade,
            "total_tokens": self.total_tokens,
            "duration_seconds": self.duration_seconds,
        }


def _truncate(text: str, max_chars: int = 3000) -> str:
    """Truncate text to stay within token budgets between agents."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...truncated for brevity]"


class ResearchPipeline:
    """Orchestrates the full multi-agent research pipeline.

    Pipeline stages:
    1. Bias Detection — analyze query for bias, produce neutral reformulation
    2. Research — gather sources using neutral queries
    3. Fact Checking — independently verify researcher claims
    4. Devil's Advocate — challenge findings adversarially
    5. Synthesis — produce final balanced report
    6. Evaluation — score the research quality quantitatively
    """

    def __init__(self, config: Config | None = None):
        self.config = config or Config.from_env()
        self.memory = MemoryStore(str(self.config.memory_dir))
        self.tools = create_default_registry()
        self._on_stage_start: list = []
        self._on_stage_complete: list = []

    def on_stage_start(self, callback):
        """Register a callback for when a pipeline stage begins."""
        self._on_stage_start.append(callback)

    def on_stage_complete(self, callback):
        """Register a callback for when a pipeline stage completes."""
        self._on_stage_complete.append(callback)

    def _notify_start(self, stage: str):
        for cb in self._on_stage_start:
            cb(stage)

    def _notify_complete(self, stage: str, result: AgentResult):
        for cb in self._on_stage_complete:
            cb(stage, result)

    def run(self, query: str) -> PipelineResult:
        """Execute the full research pipeline on a query."""
        start_time = datetime.now(timezone.utc)
        pipeline_result = PipelineResult(
            query=query,
            timestamp=start_time.isoformat(),
        )

        # Check memory for related past research
        related_topics = self.memory.get_related_topics(query)
        prior_context = ""
        if related_topics:
            for topic in related_topics[:3]:
                summary = self.memory.get_topic_summary(topic)
                prior_context += f"\nPrior research on '{topic}': {summary['entry_count']} entries, confidence range {summary.get('confidence_range', 'N/A')}\n"

        # Stage 1: Bias Detection
        self._notify_start("bias_detection")
        bias_detector = BiasDetectorAgent(self.config)
        bias_result = bias_detector.run(query, context={
            "prior_research": prior_context,
        } if prior_context else None)
        pipeline_result.stages["bias_detection"] = bias_result
        self._notify_complete("bias_detection", bias_result)

        # Extract neutral queries and required perspectives
        neutral_queries = bias_result.data.get("neutral_queries", [query])
        required_perspectives = bias_result.data.get("required_perspectives", [])
        bias_score = bias_result.data.get("bias_score", 0)

        # Stage 2: Research
        self._notify_start("research")
        researcher = ResearcherAgent(self.config, self.tools)
        research_result = researcher.run(
            "\n".join(neutral_queries),
            context={
                "original_query": query,
                "bias_analysis": f"Bias score: {bias_score}/10. Required perspectives: {', '.join(required_perspectives)}",
                "neutral_queries": json.dumps(neutral_queries),
                "required_perspectives": json.dumps(required_perspectives),
            },
        )
        pipeline_result.stages["research"] = research_result
        self._notify_complete("research", research_result)

        # Stage 3: Fact Checking
        self._notify_start("fact_checking")
        fact_checker = FactCheckerAgent(self.config, self.tools)
        fact_check_result = fact_checker.run(
            "Verify the key claims from this research:",
            context={
                "original_query": query,
                "research_findings": _truncate(research_result.content, 4000),
                "sources_found": json.dumps(research_result.data.get("sources", []))[:2000],
            },
        )
        pipeline_result.stages["fact_checking"] = fact_check_result
        self._notify_complete("fact_checking", fact_check_result)

        # Stage 4: Devil's Advocate
        self._notify_start("devils_advocate")
        devils_advocate = DevilsAdvocateAgent(self.config)
        devils_result = devils_advocate.run(
            "Challenge these research findings:",
            context={
                "original_query": query,
                "bias_analysis": _truncate(bias_result.content, 1500),
                "research_findings": _truncate(research_result.content, 4000),
                "fact_check_results": _truncate(fact_check_result.content, 2000),
            },
        )
        pipeline_result.stages["devils_advocate"] = devils_result
        self._notify_complete("devils_advocate", devils_result)

        # Stage 5: Synthesis
        self._notify_start("synthesis")
        synthesizer = SynthesizerAgent(self.config)
        synthesis_result = synthesizer.run(
            "Produce the final research report:",
            context={
                "original_query": query,
                "bias_analysis": _truncate(bias_result.content, 1500),
                "research_findings": _truncate(research_result.content, 4000),
                "fact_check_results": _truncate(fact_check_result.content, 2000),
                "challenges": _truncate(devils_result.content, 3000),
            },
        )
        pipeline_result.stages["synthesis"] = synthesis_result
        pipeline_result.final_report = synthesis_result.content
        self._notify_complete("synthesis", synthesis_result)

        # Stage 6: Evaluation
        self._notify_start("evaluation")
        evaluator = EvaluatorAgent(self.config)
        eval_result = evaluator.run(
            "Evaluate this research pipeline output:",
            context={
                "original_query": query,
                "bias_detection": _truncate(bias_result.content, 1500),
                "research": _truncate(research_result.content, 3000),
                "fact_checking": _truncate(fact_check_result.content, 2000),
                "devils_advocate": _truncate(devils_result.content, 2000),
                "final_report": _truncate(synthesis_result.content, 4000),
            },
        )
        pipeline_result.stages["evaluation"] = eval_result
        pipeline_result.evaluation_scores = eval_result.data.get("scores", {})
        pipeline_result.overall_grade = eval_result.data.get("grade", "N/A")
        self._notify_complete("evaluation", eval_result)

        # Tally tokens
        for stage_result in pipeline_result.stages.values():
            pipeline_result.total_tokens["input"] += stage_result.tokens_used.get("input", 0)
            pipeline_result.total_tokens["output"] += stage_result.tokens_used.get("output", 0)

        end_time = datetime.now(timezone.utc)
        pipeline_result.duration_seconds = (end_time - start_time).total_seconds()

        # Store key findings in memory
        self._store_to_memory(query, pipeline_result)

        return pipeline_result

    def _store_to_memory(self, query: str, result: PipelineResult):
        """Persist key findings to memory for future research context."""
        topic = query[:100].strip()

        self.memory.store(
            topic=topic,
            key="evaluation",
            value={
                "scores": result.evaluation_scores,
                "grade": result.overall_grade,
            },
            source="evaluator",
            confidence=result.evaluation_scores.get("overall_score", 0.5),
        )

        synthesis_data = result.stages.get("synthesis", None)
        if synthesis_data and synthesis_data.data:
            key_findings = synthesis_data.data.get("key_findings", [])
            for i, finding in enumerate(key_findings[:10]):
                self.memory.store(
                    topic=topic,
                    key=f"finding_{i}",
                    value=finding,
                    source="synthesizer",
                    confidence=synthesis_data.data.get("confidence_overall", 0.5),
                )
