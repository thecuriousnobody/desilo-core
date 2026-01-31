"""Simple Market Analysis Crew - Generic 4-Agent Pattern

This crew provides comprehensive market analysis using four specialized agents:
1. Market Researcher - Analyzes market size, demographics, growth
2. Trend Analyst - Identifies emerging trends and opportunities
3. Opportunity Scout - Finds market gaps and entry strategies
4. Market Validator - Synthesizes and validates findings

This is a generic implementation that works for any geography.
White-label implementations can customize by:
- Passing specific geographical_scope
- Overriding agent backstories via subclassing
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

# Load environment
load_dotenv()


class SimpleMarketCrew:
    """Simple market analysis crew using proven 4-agent pattern.

    This is a generic market analysis crew that can be used by any organization.
    Pass geographical_scope to customize the regional focus.
    """

    def __init__(self, region_context: Optional[str] = None):
        """Initialize the market crew.

        Args:
            region_context: Optional regional context for agent backstories.
                          E.g., "Austin tech ecosystem" or "Midwest business environment"
        """
        self.llm = self._create_llm()
        self.search_tool = self._create_search_tool()
        self.region_context = region_context or "startup ecosystem"

    def _create_llm(self):
        """Initialize Claude LLM with streaming enabled"""
        return LLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="anthropic/claude-haiku-4-5-20251001",
            temperature=0.3,
            max_tokens=8192,
            timeout=300,
            stream=True
        )

    def _create_search_tool(self):
        """Create Serper search tool"""
        return SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

    def get_market_researcher_backstory(self) -> str:
        """Get backstory for market researcher. Override in white-label."""
        return f"""You are an expert market researcher with 15 years of experience analyzing startup markets.
        You specialize in identifying market size, growth rates, and key demographics. You have deep knowledge
        of the {self.region_context} and broader market trends."""

    def get_trend_analyst_backstory(self) -> str:
        """Get backstory for trend analyst. Override in white-label."""
        return """You are a trend forecasting expert who identifies patterns in market data and predicts
        future developments. You excel at connecting disparate data points to reveal emerging opportunities."""

    def get_opportunity_scout_backstory(self) -> str:
        """Get backstory for opportunity scout. Override in white-label."""
        return """You are an entrepreneurial strategist who specializes in finding untapped market
        opportunities. You understand both customer pain points and competitive landscapes to identify
        viable market entry points."""

    def get_market_validator_backstory(self) -> str:
        """Get backstory for market validator. Override in white-label."""
        return """You are a senior analyst who validates research findings and ensures accuracy.
        You excel at synthesizing complex data into clear, actionable recommendations for entrepreneurs."""

    def analyze_market(
        self,
        search_terms: List[str],
        geographical_scope: List[str],
        user_message: str
    ) -> Dict[str, Any]:
        """Execute market analysis with 4 specialized agents.

        Args:
            search_terms: Keywords to research (e.g., ["fintech", "payments"])
            geographical_scope: Geographic areas (e.g., ["Austin", "Texas"])
            user_message: Context from the user about their needs

        Returns:
            Structured market analysis results
        """

        print(f"Starting market analysis for: {search_terms}")
        print(f"Geographic scope: {geographical_scope}")

        # Format geographic scope for prompts
        geo_str = ', '.join(geographical_scope) if geographical_scope else "the target market"

        # Create specialized agents
        market_researcher = Agent(
            role="Market Research Specialist",
            goal=f"Analyze the market size and potential for {', '.join(search_terms)} in {geo_str}",
            backstory=self.get_market_researcher_backstory(),
            llm=self.llm,
            tools=[self.search_tool],
            verbose=False
        )

        trend_analyst = Agent(
            role="Market Trend Analyst",
            goal="Identify emerging trends and future opportunities in the target market",
            backstory=self.get_trend_analyst_backstory(),
            llm=self.llm,
            tools=[self.search_tool],
            verbose=False
        )

        opportunity_scout = Agent(
            role="Opportunity Scout",
            goal="Identify specific market gaps and opportunities for new entrants",
            backstory=self.get_opportunity_scout_backstory(),
            llm=self.llm,
            tools=[self.search_tool],
            verbose=False
        )

        market_validator = Agent(
            role="Market Analysis Validator",
            goal="Validate and synthesize market research findings into actionable insights",
            backstory=self.get_market_validator_backstory(),
            llm=self.llm,
            tools=[self.search_tool],
            verbose=False
        )

        # Create tasks
        market_size_task = Task(
            description=f"""Analyze the market size and demographics for {', '.join(search_terms)} in {geo_str}.

            Research and provide:
            1. Total addressable market (TAM) size with specific numbers
            2. Serviceable addressable market (SAM)
            3. Key customer demographics and segments
            4. Market growth rate and projections (include percentages)
            5. Revenue potential and pricing models
            6. Cite credible sources for all data

            Focus on: {user_message}
            """,
            expected_output="""Market analysis report with specific numbers:
            - Market Size: TAM/SAM with dollar amounts
            - Growth Rate: Annual percentage growth
            - Demographics: Target customer profiles
            - Revenue Potential: Realistic financial projections
            - Sources: URLs and citations for all data""",
            agent=market_researcher
        )

        trends_task = Task(
            description=f"""Identify key trends and future developments for {', '.join(search_terms)} market.

            Research:
            1. Emerging technologies and innovations
            2. Changing customer behaviors and preferences
            3. Regulatory changes and their impact
            4. Competitive landscape evolution
            5. Future growth drivers and market shifts

            Context: {user_message}
            """,
            expected_output="""Trend analysis report:
            - Current Trends: Top 5 market trends with evidence
            - Emerging Opportunities: Future developments timeline
            - Risk Factors: Potential challenges and threats
            - Market Drivers: Key factors driving growth""",
            agent=trend_analyst
        )

        opportunities_task = Task(
            description=f"""Identify specific market opportunities for {', '.join(search_terms)} startup.

            Find:
            1. Unmet customer needs and pain points
            2. Market gaps not addressed by current competitors
            3. Partnership opportunities in {geo_str}
            4. Entry strategies for new market players
            5. Local resources and connections in the target region

            User context: {user_message}
            """,
            expected_output="""Opportunity analysis:
            - Market Gaps: Specific unmet customer needs
            - Entry Strategies: Recommended market entry approaches
            - Local Partnerships: Regional collaboration opportunities
            - Differentiation: Unique value proposition ideas
            - Quick Wins: Immediate market opportunities""",
            agent=opportunity_scout
        )

        validation_task = Task(
            description="""Validate all market research findings and create comprehensive recommendations.

            Synthesize and validate:
            1. Cross-verify all market data and statistics
            2. Ensure recommendations are actionable and specific
            3. Identify key risks and mitigation strategies
            4. Prioritize next steps based on findings
            5. Highlight region-specific resources and opportunities
            """,
            expected_output="""Validated market analysis summary:
            - Executive Summary: Key findings in bullet points
            - Market Validation: Cross-checked data with confidence levels
            - Strategic Recommendations: Top 5 prioritized action items
            - Risk Assessment: Major risks with mitigation strategies
            - Local Resources: Region-specific opportunities and contacts
            - Next Steps: Prioritized implementation roadmap""",
            agent=market_validator
        )

        # Create and execute crew
        crew = Crew(
            agents=[market_researcher, trend_analyst, opportunity_scout, market_validator],
            tasks=[market_size_task, trends_task, opportunities_task, validation_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()

        return self._process_results(result, search_terms, geographical_scope)

    def _process_results(
        self,
        crew_result,
        search_terms: List[str],
        geographical_scope: List[str]
    ) -> Dict[str, Any]:
        """Process crew results into structured format"""

        result_str = str(crew_result)

        processed = {
            "analysis_type": "market_analysis",
            "search_terms": search_terms,
            "geographical_scope": geographical_scope,
            "raw_output": result_str,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Extract market size data
        import re
        market_size_match = re.search(
            r'(?:Market Size|TAM|Total.*Market):.*?(\$[\d,]+[KMB]?)',
            result_str, re.IGNORECASE
        )
        if market_size_match:
            processed["market_size"] = market_size_match.group(1)

        # Extract growth rate
        growth_match = re.search(
            r'(?:Growth Rate|Growth):.*?([\d.]+%)',
            result_str, re.IGNORECASE
        )
        if growth_match:
            processed["growth_rate"] = growth_match.group(1)

        # Extract trends
        trends_section = re.search(
            r'(?:Current Trends|Market Trends|Trends):(.+?)(?:\n\n|\n[A-Z])',
            result_str, re.DOTALL | re.IGNORECASE
        )
        trends = []
        if trends_section:
            trend_items = re.findall(r'(?:\d+\.|[-])\s*(.+)', trends_section.group(1))
            trends = [item.strip() for item in trend_items[:5]]
        processed["market_trends"] = trends

        # Extract opportunities
        opp_section = re.search(
            r'(?:Market Gaps|Opportunities|Market Opportunities):(.+?)(?:\n\n|\n[A-Z])',
            result_str, re.DOTALL | re.IGNORECASE
        )
        opportunities = []
        if opp_section:
            opp_items = re.findall(r'(?:\d+\.|[-])\s*(.+)', opp_section.group(1))
            opportunities = [
                {"opportunity": item.strip(), "type": "market_gap"}
                for item in opp_items[:5]
            ]
        processed["opportunities"] = opportunities

        # Extract recommendations
        rec_section = re.search(
            r'(?:Recommendations|Strategic Recommendations|Action Items):(.+?)(?:\n\n|\n[A-Z])',
            result_str, re.DOTALL | re.IGNORECASE
        )
        recommendations = []
        if rec_section:
            rec_items = re.findall(r'(?:\d+\.|[-])\s*(.+)', rec_section.group(1))
            recommendations = [item.strip() for item in rec_items[:5]]
        processed["recommendations"] = recommendations

        # Extract URLs as sources
        urls = re.findall(r'https?://[^\s<>"{}|\\^\[\]`]+', result_str)
        processed["sources"] = [
            {"url": url, "type": "web", "extracted_from": "crew_output"}
            for url in urls[:10]
        ]

        # Calculate confidence based on data completeness
        confidence = 0.5
        if processed.get("market_size"):
            confidence += 0.1
        if processed.get("growth_rate"):
            confidence += 0.1
        if processed.get("market_trends"):
            confidence += 0.1
        if processed.get("opportunities"):
            confidence += 0.1
        if processed.get("sources"):
            confidence += 0.1
        processed["confidence"] = min(confidence, 1.0)

        return {
            "status": "success",
            "data": processed,
            "confidence": processed["confidence"],
            "sources": processed["sources"]
        }


# Test function
async def test_simple_crew():
    """Test the simple market crew with generic data"""

    print("Testing Simple Market Crew")
    print("=" * 50)

    crew = SimpleMarketCrew(region_context="startup ecosystem")

    result = crew.analyze_market(
        search_terms=["AI startup", "artificial intelligence", "machine learning"],
        geographical_scope=["United States"],
        user_message="I'm building an AI startup. I need comprehensive market analysis."
    )

    print("\n" + "=" * 50)
    print("CREW EXECUTION COMPLETE!")
    print("=" * 50)

    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Sources found: {len(result.get('sources', []))}")

    return result


if __name__ == "__main__":
    result = asyncio.run(test_simple_crew())

    with open('crew_test_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nFull results saved to: crew_test_results.json")
