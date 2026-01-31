"""
Search Adapter Contract

Defines the interface for search capabilities.
Core provides some adapters (SerperDev), white-label can add custom ones.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class SearchSource(Enum):
    """Known search sources."""
    WEB = "web"
    LINKEDIN = "linkedin"
    CRUNCHBASE = "crunchbase"
    NEWS = "news"
    ACADEMIC = "academic"
    CUSTOM = "custom"


@dataclass
class SearchResult:
    """
    Standard search result format.
    ALL search adapters must return results in this format.
    """
    title: str
    url: str
    snippet: str
    source: str  # Identifier for the search source
    relevance_score: float = 0.0
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata or {}
        }


class SearchAdapter(ABC):
    """
    CONTRACT: Interface for search capabilities.

    This is a STABLE interface - we commit to not changing it
    without a major version bump and deprecation period.

    Example:
        class SerperSearchAdapter(SearchAdapter):
            async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
                # Call Serper API
                ...

        class LinkedInAdapter(SearchAdapter):
            async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
                # Scrape LinkedIn
                ...
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[SearchResult]:
        """
        Execute a search and return standardized results.

        Args:
            query: The search query string
            limit: Maximum number of results to return
            filters: Optional filters (source-specific)

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Return True if the adapter is operational.
        Used for monitoring and fallback logic.
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return identifier for this search source."""
        pass

    def get_source_type(self) -> SearchSource:
        """Return the type of search source. Override if needed."""
        return SearchSource.CUSTOM

    async def search_with_fallback(
        self,
        query: str,
        limit: int = 10,
        fallback_adapters: Optional[List['SearchAdapter']] = None
    ) -> List[SearchResult]:
        """
        Search with automatic fallback to other adapters if this one fails.
        """
        try:
            if await self.health_check():
                return await self.search(query, limit)
        except Exception:
            pass

        # Try fallbacks
        if fallback_adapters:
            for adapter in fallback_adapters:
                try:
                    if await adapter.health_check():
                        return await adapter.search(query, limit)
                except Exception:
                    continue

        return []  # All adapters failed
