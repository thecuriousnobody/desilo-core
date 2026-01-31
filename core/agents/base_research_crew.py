"""Base Research Crew for DeSilo Core

This provides the foundation for all specialized research crews with
reasoning capabilities and guardrails. White-label implementations
extend this base class to create organization-specific research crews.
"""

import os
import logging
from abc import abstractmethod
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, before_kickoff, crew, task
from dotenv import load_dotenv

from datetime import datetime

logger = logging.getLogger(__name__)


class BaseResearchCrew(CrewBase):
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

    # Config paths relative to crew file - override in subclasses
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, region: Optional[str] = None):
        """Initialize the research crew.

        Args:
            region: Optional region for local searches. If not provided,
                   searches will be generic (no geographic focus).
        """
        self.inputs = {}
        self.request = None
        self._region = region

        # Load environment
        self._load_environment()

        # Initialize LLM with reasoning capabilities
        self.llm = self._initialize_llm()

        # Initialize search tools
        self.search_tools = self._initialize_search_tools()

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
        # Try common paths
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

    def _initialize_llm(self):
        """Initialize LLM with appropriate settings"""
        return LLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="anthropic/claude-haiku-4-5-20251001",
            temperature=0.3,
            max_tokens=8192,
            timeout=300
        )

    def _initialize_search_tools(self):
        """Initialize search tools using SerperDev"""
        from crewai_tools import SerperDevTool
        from crewai.tools import tool

        # Initialize SerperDev
        serper = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

        # Capture region for closure
        region = self.get_region()

        @tool("Search the web for information")
        def web_search(search_query: str) -> str:
            """Search the web for current information"""
            return serper.run(search_query)

        @tool("Search for local resources")
        def local_search(search_query: str) -> str:
            """Search specifically for local/regional resources"""
            if region:
                query = f"{region} {search_query}"
            else:
                query = search_query
            return serper.run(query)

        @tool("Search for industry insights")
        def industry_search(search_query: str) -> str:
            """Search for industry-specific insights and trends"""
            query = f"industry analysis trends {search_query}"
            return serper.run(query)

        return {
            "web_search": web_search,
            "local_search": local_search,
            "industry_search": industry_search
        }

    @before_kickoff
    def prepare_inputs(self, inputs):
        """Prepare inputs before crew execution"""
        if 'request' not in inputs:
            raise ValueError("Request is required in inputs")

        self.request = inputs['request']
        self.inputs = inputs
        return inputs

    def validate_output(self, result: Any, expected_structure: Dict[str, type]) -> Tuple[bool, str]:
        """Validate output against expected structure

        This is a guardrail to ensure output quality.
        """
        try:
            result_str = str(result)

            # Check for required keys in the output
            missing_keys = []
            for key, expected_type in expected_structure.items():
                if key not in result_str:
                    missing_keys.append(key)

            if missing_keys:
                return (False, f"Missing required sections: {', '.join(missing_keys)}")

            return (True, result_str)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return (False, f"Validation failed: {str(e)}")

    @abstractmethod
    def get_research_agents(self) -> List[Agent]:
        """Get the list of agents for this research type

        Each specialized crew must implement this.
        """
        pass

    @abstractmethod
    def get_research_tasks(self) -> List[Task]:
        """Get the list of tasks for this research type

        Each specialized crew must implement this.
        """
        pass

    @crew
    def crew(self) -> Crew:
        """Create the crew with all agents and tasks"""
        return Crew(
            agents=self.get_research_agents(),
            tasks=self.get_research_tasks(),
            verbose=True,
            process=Process.sequential,
            max_retry_attempts=3,
            retry_wait_time=5
        )

    def process_output(self, output) -> Dict[str, Any]:
        """Process crew output into structured format"""
        if not output:
            return {
                "status": "error",
                "message": "No output generated"
            }

        try:
            # Extract structured data from output
            result = self._extract_structured_data(str(output))

            return {
                "status": "success",
                "data": result,
                "confidence": self._calculate_confidence(result),
                "sources": self._extract_sources(str(output))
            }

        except Exception as e:
            logger.error(f"Error processing output: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _extract_structured_data(self, output: str) -> Dict[str, Any]:
        """Extract structured data from crew output

        Override in specialized crews for custom extraction.
        """
        # Default implementation
        return {
            "raw_output": output,
            "extracted_at": str(datetime.utcnow())
        }

    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for the results

        Based on completeness and quality of data.
        """
        confidence = 0.5

        if result.get("raw_output"):
            confidence += 0.2

        if result.get("sources"):
            confidence += 0.3

        return min(confidence, 1.0)

    def _extract_sources(self, output: str) -> List[Dict[str, str]]:
        """Extract sources from the output"""
        sources = []

        import re
        url_pattern = r'https?://[^\s<>"{}|\\^\[\]`]+'
        urls = re.findall(url_pattern, output)

        for url in urls[:10]:
            sources.append({
                "url": url,
                "type": "web",
                "extracted_from": "crew_output"
            })

        return sources
