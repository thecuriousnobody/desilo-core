"""
DeSilo Core Contracts

These abstract base classes define the interfaces between the open-source core
and white-label implementations. White-label partners implement these contracts
to customize the platform for their specific needs.

The contracts are STABLE - we commit to backward compatibility.
Breaking changes require a major version bump.
"""

from .agent import AgentPersona
from .search import SearchAdapter, SearchResult
from .resources import ResourceConnector, Resource
from .knowledge import KnowledgeBase, Insight
from .tenant import TenantConfig
from .events import EventStore, ScrapedEvent

__all__ = [
    'AgentPersona',
    'SearchAdapter',
    'SearchResult',
    'ResourceConnector',
    'Resource',
    'KnowledgeBase',
    'Insight',
    'TenantConfig',
    'EventStore',
    'ScrapedEvent',
]
