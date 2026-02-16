"""
Event Store Contract

Defines the interface for storing and querying scraped events.
White-label implementations provide their own storage backends
(PostgreSQL, SQLite, DynamoDB, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class ScrapedEvent:
    """
    Standard event format across all white-label deployments.

    All event storage backends must accept and return events in this format.
    Dates should be ISO format (YYYY-MM-DD) when possible.
    """
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    organization: str = ""
    organization_full: Optional[str] = None
    description: Optional[str] = None
    original_link: Optional[str] = None
    event_type: str = "event"
    source_platform: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "date": self.date,
            "time": self.time,
            "location": self.location,
            "organization": self.organization,
            "organization_full": self.organization_full,
            "description": self.description,
            "original_link": self.original_link,
            "event_type": self.event_type,
            "source_platform": self.source_platform,
            "image_url": self.image_url,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapedEvent":
        return cls(
            title=data.get("title", ""),
            date=data.get("date"),
            time=data.get("time"),
            location=data.get("location"),
            organization=data.get("organization", ""),
            organization_full=data.get("organization_full"),
            description=data.get("description"),
            original_link=data.get("original_link"),
            event_type=data.get("event_type", "event"),
            source_platform=data.get("source_platform"),
            image_url=data.get("image_url"),
            metadata=data.get("metadata", {}),
        )


class EventStore(ABC):
    """
    CONTRACT: Interface for event storage backends.

    White-label implementations must implement this to provide
    persistent event storage. Events are typically populated by
    social media scrapers and consumed by chat agents.

    Example:
        class PostgresEventStore(EventStore):
            async def save_events(self, events, source_id=None):
                # INSERT into scraped_events table
                ...

        class SQLiteEventStore(EventStore):
            async def save_events(self, events, source_id=None):
                # INSERT into local SQLite
                ...
    """

    @abstractmethod
    async def save_events(
        self,
        events: List[ScrapedEvent],
        source_id: Optional[str] = None,
    ) -> int:
        """
        Save events to the store. Returns count of saved events.

        Args:
            events: List of ScrapedEvent objects to save.
            source_id: Optional identifier for the source (e.g., brief_id).

        Returns:
            Number of events successfully saved.
        """
        pass

    @abstractmethod
    async def get_upcoming_events(
        self,
        days_ahead: int = 30,
        organization: Optional[str] = None,
        limit: int = 50,
    ) -> List[ScrapedEvent]:
        """
        Get upcoming events from the store.

        Args:
            days_ahead: How many days into the future to look.
            organization: Optional filter by organization name.
            limit: Maximum number of events to return.

        Returns:
            List of ScrapedEvent objects, ordered by date ascending.
        """
        pass

    @abstractmethod
    async def init_store(self) -> bool:
        """
        Initialize the storage backend (create tables, indexes, etc.).

        Returns:
            True if initialization succeeded.
        """
        pass
