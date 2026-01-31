"""Base Research Crew for DeSilo Core

This provides the foundation for all specialized research crews.
White-label implementations extend this base class to create
organization-specific research crews.
"""

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone

from crewai import LLM, Agent, Crew, Process, Task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class BaseResearchCrew(ABC):
    """Base class for all research crews with common functionality.

    This is a generic base class that can be extended by any organization.
    It provides:
    - LLM initialization with Claude models
    - Search tool initialization with configurable region
    - Input validation and preparation
    - Output processing and confidence scoring

    Override `get_region()` in white-label implementations to customize
    the geographic focus of local searches.
    """

    def __init__(self, region: Optional[str] = None):
        """Initialize the research crew.

        Args:
            region: Optional region for local searches. If not provided,
                   searches will be generic (no geographic focus).
        """
        self._region = region

        # Load environment
        self._load_environment()

        # Initialize LLM with reasoning capabilities
        self.llm = self._initialize_llm()

        # Initialize search tool
        self.search_tool = self._initialize_search_tool()

    def get_region(self) -> Optional[str]:
        """Get the region for local searches.

        Override this in white-label implementations to return
        the organization's geographic focus.

        Returns:
            Region string (e.g., "Austin Metro Area") or None for generic
        """
        return self._region

    def _load_environment(self):
        """Load environment variables"""
        env_paths = [
            Path('.env'),
            Path('.env.production'),
            Path('/app/.env'),
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
                break

    def _initialize_llm(self) -> LLM:
        """Initialize LLM with appropriate settings"""
        return LLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="anthropic/claude-haiku-4-5-20251001",
            temperature=0.3,
            max_tokens=8192,
            timeout=300
        )

    def _initialize_search_tool(self) -> SerperDevTool:
        """Initialize SerperDev search tool"""
        return SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

    @abstractmethod
    def get_agents(self) -> List[Agent]:
        """Get the list of agents for this research crew.

        Each specialized crew must implement this.
        """
        pass

    @abstractmethod
    def get_tasks(self, **kwargs) -> List[Task]:
        """Get the list of tasks for this research crew.

        Each specialized crew must implement this.

        Args:
            **kwargs: Task-specific parameters (e.g., search_terms, user_message)
        """
        pass

    def create_crew(self) -> Crew:
        """Create the crew with all agents and tasks"""
        return Crew(
            agents=self.get_agents(),
            tasks=self.get_tasks(),
            verbose=False,
            process=Process.sequential
        )

    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the research crew.

        Args:
            **kwargs: Parameters passed to get_tasks()

        Returns:
            Processed results dictionary
        """
        try:
            crew = Crew(
                agents=self.get_agents(),
                tasks=self.get_tasks(**kwargs),
                verbose=False,
                process=Process.sequential
            )

            result = crew.kickoff()
            return self.process_output(result)

        except Exception as e:
            logger.error(f"Crew execution error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def process_output(self, output) -> Dict[str, Any]:
        """Process crew output into structured format"""
        if not output:
            return {
                "status": "error",
                "message": "No output generated"
            }

        try:
            output_str = str(output)
            result = self._extract_structured_data(output_str)

            return {
                "status": "success",
                "data": result,
                "confidence": self._calculate_confidence(result),
                "sources": self._extract_sources(output_str)
            }

        except Exception as e:
            logger.error(f"Error processing output: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _extract_structured_data(self, output: str) -> Dict[str, Any]:
        """Extract structured data from crew output.

        Override in specialized crews for custom extraction.
        """
        return {
            "raw_output": output,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }

    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for the results."""
        confidence = 0.5

        if result.get("raw_output"):
            confidence += 0.2

        if result.get("sources"):
            confidence += 0.3

        return min(confidence, 1.0)

    def _extract_sources(self, output: str) -> List[Dict[str, str]]:
        """Extract sources/URLs from the output"""
        sources = []
        url_pattern = r'https?://[^\s<>"{}|\\^\[\]`]+'
        urls = re.findall(url_pattern, output)

        for url in urls[:10]:
            sources.append({
                "url": url,
                "type": "web",
                "extracted_from": "crew_output"
            })

        return sources
