"""
Resource Connector Contract

Defines the interface for connecting startups with local resources.
White-label implementations provide region-specific resource databases.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class ResourceType(Enum):
    """Types of startup resources."""
    FUNDING = "funding"
    MENTOR = "mentor"
    SERVICE = "service"  # Legal, accounting, etc.
    EVENT = "event"
    ACCELERATOR = "accelerator"
    COWORKING = "coworking"
    GOVERNMENT = "government"  # Grants, permits, etc.
    EDUCATION = "education"
    NETWORK = "network"
    OTHER = "other"


class FundingStage(Enum):
    """Startup funding stages."""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"
    GRANT = "grant"
    BOOTSTRAPPED = "bootstrapped"


@dataclass
class Resource:
    """
    Standard resource format.
    ALL resource connectors must return resources in this format.
    """
    id: str
    name: str
    resource_type: ResourceType
    description: str
    url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    location: Optional[str] = None
    industries: Optional[List[str]] = None
    funding_stages: Optional[List[FundingStage]] = None
    relevance_score: float = 0.0
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "resource_type": self.resource_type.value,
            "description": self.description,
            "url": self.url,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "location": self.location,
            "industries": self.industries or [],
            "funding_stages": [s.value for s in (self.funding_stages or [])],
            "relevance_score": self.relevance_score,
            "metadata": self.metadata or {}
        }


class ResourceConnector(ABC):
    """
    CONTRACT: Interface for regional resource databases.

    White-label implementations must implement this to provide
    region-specific resources (funding, mentors, services, etc.).

    Example:
        class AustinResources(ResourceConnector):
            async def find_resources(self, ...) -> List[Resource]:
                # Return Austin-area resources
                ...
    """

    @abstractmethod
    async def find_resources(
        self,
        industry: Optional[str] = None,
        stage: Optional[FundingStage] = None,
        resource_types: Optional[List[ResourceType]] = None,
        limit: int = 20
    ) -> List[Resource]:
        """
        Find relevant resources for a startup.

        Args:
            industry: Filter by industry (e.g., "fintech", "healthcare")
            stage: Filter by funding stage
            resource_types: Filter by resource types
            limit: Maximum results to return

        Returns:
            List of Resource objects
        """
        pass

    @abstractmethod
    async def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a specific resource by ID."""
        pass

    @abstractmethod
    def get_supported_industries(self) -> List[str]:
        """Return list of industries this connector has resources for."""
        pass

    @abstractmethod
    def get_region_name(self) -> str:
        """Return the name of the region this connector covers."""
        pass

    async def search_resources(
        self,
        query: str,
        limit: int = 20
    ) -> List[Resource]:
        """
        Free-text search for resources.
        Default implementation - can be overridden for better search.
        """
        # Default: get all resources and filter by query
        all_resources = await self.find_resources(limit=100)
        query_lower = query.lower()
        matching = [
            r for r in all_resources
            if query_lower in r.name.lower() or query_lower in r.description.lower()
        ]
        return matching[:limit]
