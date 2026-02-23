"""
Tenant Configuration Contract

Defines the interface for multi-tenant configuration.
Each white-label deployment is a "tenant" with its own settings.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BrandingConfig:
    """Visual branding configuration for a tenant."""
    organization_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#000000"
    secondary_color: str = "#ffffff"
    font_family: str = "Inter, sans-serif"


@dataclass
class RegionConfig:
    """Geographic configuration for a tenant."""
    region_name: str  # "Austin Metro", "San Francisco Bay Area", etc.
    cities: List[str] = field(default_factory=list)
    state: Optional[str] = None
    country: str = "USA"
    search_radius_miles: int = 50


@dataclass
class FeatureFlags:
    """Feature toggles for a tenant."""
    enable_voice: bool = False
    enable_avatar: bool = False
    enable_deep_research: bool = True
    enable_calendar_optimizer: bool = False
    enable_civic_solver: bool = False
    enable_email_resources: bool = False
    enable_workflow_approval: bool = True


@dataclass
class TenantConfig:
    """
    Complete configuration for a white-label tenant.

    This is the master configuration object that brings together
    all tenant-specific settings. The core platform reads this
    to customize behavior for each deployment.

    Example:
        my_config = TenantConfig(
            tenant_id="my-accelerator",
            branding=BrandingConfig(
                organization_name="My Accelerator",
                primary_color="#1a1a1a",
            ),
            region=RegionConfig(
                region_name="Austin Metro",
                cities=["Austin", "Round Rock", "Cedar Park"],
                state="Texas",
            ),
            persona_class="my_personas.MyAssistant",
            resource_connector_class="austin_resources.AustinResourceConnector",
            knowledge_base_class="my_knowledge.MyKnowledgeBase",
        )
    """
    # Required
    tenant_id: str
    branding: BrandingConfig
    region: RegionConfig

    # Class paths for dependency injection
    # Format: "module.path.ClassName"
    persona_class: str = ""
    resource_connector_class: str = ""
    knowledge_base_class: str = ""
    search_adapter_classes: List[str] = field(default_factory=list)

    # Optional settings
    features: FeatureFlags = field(default_factory=FeatureFlags)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    # API configuration (stored in environment, referenced here)
    llm_model: str = "claude-sonnet-4-20250514"
    search_api: str = "serper"  # "serper", "serpapi", "custom"

    def get_full_region_name(self) -> str:
        """Return full region name including state/country."""
        if self.region.state:
            return f"{self.region.region_name}, {self.region.state}"
        return self.region.region_name

    def to_dict(self) -> dict:
        """Serialize config to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "branding": {
                "organization_name": self.branding.organization_name,
                "logo_url": self.branding.logo_url,
                "primary_color": self.branding.primary_color,
                "secondary_color": self.branding.secondary_color,
                "font_family": self.branding.font_family,
            },
            "region": {
                "region_name": self.region.region_name,
                "cities": self.region.cities,
                "state": self.region.state,
                "country": self.region.country,
                "search_radius_miles": self.region.search_radius_miles,
            },
            "features": {
                "enable_voice": self.features.enable_voice,
                "enable_avatar": self.features.enable_avatar,
                "enable_deep_research": self.features.enable_deep_research,
                "enable_calendar_optimizer": self.features.enable_calendar_optimizer,
                "enable_civic_solver": self.features.enable_civic_solver,
                "enable_email_resources": self.features.enable_email_resources,
            },
            "persona_class": self.persona_class,
            "resource_connector_class": self.resource_connector_class,
            "knowledge_base_class": self.knowledge_base_class,
            "search_adapter_classes": self.search_adapter_classes,
            "llm_model": self.llm_model,
            "search_api": self.search_api,
            "custom_settings": self.custom_settings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TenantConfig':
        """Create config from dictionary."""
        return cls(
            tenant_id=data["tenant_id"],
            branding=BrandingConfig(**data.get("branding", {})),
            region=RegionConfig(**data.get("region", {})),
            features=FeatureFlags(**data.get("features", {})),
            persona_class=data.get("persona_class", ""),
            resource_connector_class=data.get("resource_connector_class", ""),
            knowledge_base_class=data.get("knowledge_base_class", ""),
            search_adapter_classes=data.get("search_adapter_classes", []),
            llm_model=data.get("llm_model", "claude-sonnet-4-20250514"),
            search_api=data.get("search_api", "serper"),
            custom_settings=data.get("custom_settings", {}),
        )
