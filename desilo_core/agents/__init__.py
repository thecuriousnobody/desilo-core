"""
DeSilo Core Agents

Generic CrewAI agent patterns for startup research and analysis.
"""

from .base_research_crew import BaseResearchCrew
from .simple_market_crew import SimpleMarketCrew

__all__ = [
    'BaseResearchCrew',
    'SimpleMarketCrew',
]
