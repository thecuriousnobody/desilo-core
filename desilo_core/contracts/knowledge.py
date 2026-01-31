"""
Knowledge Base Contract

Defines the interface for proprietary knowledge/RAG systems.
White-label implementations provide their own knowledge bases.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Insight:
    """
    An insight from the knowledge base.
    Could be from past conversations, documents, or curated data.
    """
    id: str
    content: str
    source: str  # "conversation", "document", "curated"
    industry: Optional[str] = None
    relevance_score: float = 0.0
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "industry": self.industry,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata or {}
        }


@dataclass
class ConversationMemory:
    """A stored conversation for RAG retrieval."""
    id: str
    user_id: str
    messages: List[dict]
    industry: Optional[str] = None
    startup_stage: Optional[str] = None
    key_topics: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class KnowledgeBase(ABC):
    """
    CONTRACT: Interface for proprietary knowledge systems.

    White-label implementations provide their own knowledge bases
    containing historical conversations, curated insights, etc.

    Example:
        class MyKnowledgeBase(KnowledgeBase):
            # Your organization's historical data and insights
            async def get_insights(self, topic: str) -> List[Insight]:
                ...
    """

    @abstractmethod
    async def get_insights(
        self,
        topic: str,
        industry: Optional[str] = None,
        limit: int = 10
    ) -> List[Insight]:
        """
        Retrieve relevant insights for a topic.

        Args:
            topic: The topic to search for
            industry: Optional industry filter
            limit: Maximum insights to return

        Returns:
            List of Insight objects, ranked by relevance
        """
        pass

    @abstractmethod
    async def store_conversation(
        self,
        conversation: ConversationMemory
    ) -> str:
        """
        Store a conversation for future RAG retrieval.

        Args:
            conversation: The conversation to store

        Returns:
            The ID of the stored conversation
        """
        pass

    @abstractmethod
    async def get_industry_patterns(
        self,
        industry: str
    ) -> List[Insight]:
        """
        Get aggregated patterns/insights for an industry.
        """
        pass

    @abstractmethod
    async def get_funding_insights(
        self,
        industry: str,
        stage: str
    ) -> List[Insight]:
        """
        Get funding-specific insights.
        """
        pass

    def get_knowledge_base_name(self) -> str:
        """Return the name of this knowledge base. Override in implementation."""
        return "Generic Knowledge Base"

    async def health_check(self) -> bool:
        """Check if the knowledge base is operational."""
        try:
            # Try to retrieve something
            await self.get_insights("test", limit=1)
            return True
        except Exception:
            return False
