"""
Agent Persona Contract

Defines the interface for conversational AI personas.
White-label implementations provide their own custom personas.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ConversationStyle:
    """Configuration for how the agent communicates."""
    max_sentences_per_response: int = 2
    tone: str = "professional"  # "professional", "casual", "friendly"
    energy: str = "warm"  # "warm", "energetic", "calm"


@dataclass
class PersonaConfig:
    """Complete persona configuration."""
    name: str
    role: str
    goal: str
    backstory: str
    style: ConversationStyle
    opening_messages: List[str]
    listening_signals: List[str]
    progression_phrases: List[str]
    never_do: List[str]
    always_do: List[str]


class AgentPersona(ABC):
    """
    CONTRACT: Interface for conversational AI personas.

    White-label implementations must implement this to define their
    organization's intake specialist or assistant persona.

    Example:
        class MyAssistant(AgentPersona):
            def get_config(self) -> PersonaConfig:
                return PersonaConfig(
                    name="Alex",
                    role="Startup Intake Specialist",
                    ...
                )
    """

    @abstractmethod
    def get_config(self) -> PersonaConfig:
        """Return the complete persona configuration."""
        pass

    @abstractmethod
    def get_backstory(self) -> str:
        """Return the persona's backstory for agent initialization."""
        pass

    @abstractmethod
    def get_opening_message(self) -> str:
        """Return a greeting message to start conversations."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the full system prompt for the LLM."""
        pass

    def get_conversation_style(self) -> ConversationStyle:
        """Return conversation style settings. Can be overridden."""
        return self.get_config().style

    def should_trigger_search(self, message: str) -> bool:
        """
        Determine if a user message should trigger a proactive search.
        Override to customize search trigger logic.
        """
        # Default implementation - override in white-label
        search_triggers = [
            "market", "competition", "funding", "investors",
            "demographics", "location", "events"
        ]
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in search_triggers)
