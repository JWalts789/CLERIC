"""CLERIC agent layer: specialized agents for unbiased multi-perspective research."""

from cleric.agents.base import AgentResult, BaseAgent
from cleric.agents.bias_detector import BiasDetectorAgent
from cleric.agents.researcher import ResearcherAgent
from cleric.agents.fact_checker import FactCheckerAgent
from cleric.agents.devils_advocate import DevilsAdvocateAgent
from cleric.agents.synthesizer import SynthesizerAgent
from cleric.agents.evaluator import EvaluatorAgent

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
