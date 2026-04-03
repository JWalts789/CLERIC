"""Verity agent layer: specialized agents for unbiased multi-perspective research."""

from verity.agents.base import AgentResult, BaseAgent
from verity.agents.bias_detector import BiasDetectorAgent
from verity.agents.researcher import ResearcherAgent
from verity.agents.fact_checker import FactCheckerAgent
from verity.agents.devils_advocate import DevilsAdvocateAgent
from verity.agents.synthesizer import SynthesizerAgent
from verity.agents.evaluator import EvaluatorAgent

__all__ = [
    "AgentResult",
    "BaseAgent",
    "BiasDetectorAgent",
    "ResearcherAgent",
    "FactCheckerAgent",
    "DevilsAdvocateAgent",
    "SynthesizerAgent",
    "EvaluatorAgent",
]
