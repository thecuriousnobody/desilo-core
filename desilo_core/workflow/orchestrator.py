"""
Default Workflow Orchestrator

Implements the deterministic clarify-plan-execute workflow:
1. Clarify - Use Haiku to generate targeted clarifying questions
2. Plan - Use Haiku to generate a research plan from user answers
3. Execute - Run CrewAI agents with the refined scope
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional

from crewai import LLM
from dotenv import load_dotenv

from desilo_core.contracts.workflow import (
    WorkflowOrchestrator, WorkflowState, WorkflowPhase,
    ClarifyingQuestion, ResearchPlan, ResearchPlanStep,
    StartupContextStore, StartupContext
)
from desilo_core.agents.simple_market_crew import SimpleMarketCrew

load_dotenv()
logger = logging.getLogger(__name__)


class DefaultOrchestrator(WorkflowOrchestrator):
    """
    Default implementation of the deterministic workflow.

    Uses a lightweight Haiku LLM call to generate clarifying questions
    and research plans before executing expensive CrewAI research.

    Args:
        context_store: Store for retrieving past startup contexts.
        crew: Optional pre-configured SimpleMarketCrew. If None, one is
              created during execution using plan parameters.
        llm: Optional pre-configured LLM for question/plan generation.
             If None, creates a Haiku instance.
    """

    def __init__(
        self,
        context_store: StartupContextStore,
        crew: Optional[SimpleMarketCrew] = None,
        llm: Optional[LLM] = None
    ):
        self._context_store = context_store
        self._crew = crew
        self._llm = llm or self._create_llm()
        self._workflows: Dict[str, WorkflowState] = {}

    def _create_llm(self) -> LLM:
        """Create lightweight LLM for question/plan generation."""
        return LLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="anthropic/claude-haiku-4-5-20251001",
            temperature=0.3,
            max_tokens=2048,
            timeout=30
        )

    async def start(self, user_id: str, user_message: str) -> WorkflowState:
        workflow_id = str(uuid.uuid4())

        # Retrieve existing startup contexts
        existing_startups = await self._context_store.get_user_startups(user_id)

        # Generate clarifying questions using LLM
        questions = await self._generate_questions(user_message, existing_startups)

        state = WorkflowState(
            workflow_id=workflow_id,
            phase=WorkflowPhase.CLARIFY,
            user_message=user_message,
            clarifying_questions=questions,
            available_startups=existing_startups if existing_startups else None
        )

        self._workflows[workflow_id] = state
        return state

    async def answer_questions(
        self, workflow_id: str, answers: Dict[str, str]
    ) -> WorkflowState:
        state = self._workflows[workflow_id]

        if state.phase != WorkflowPhase.CLARIFY:
            raise ValueError(
                f"Cannot answer questions in phase '{state.phase.value}'. "
                f"Expected phase: 'clarify'"
            )

        state.user_answers = answers

        # If user selected an existing startup, load it
        startup_id = answers.get("startup_selection")
        if startup_id:
            startup = await self._context_store.get_startup_by_id(startup_id)
            state.startup_context = startup

        # Generate research plan using LLM
        plan = await self._generate_plan(state.user_message, answers, state.startup_context)
        state.plan = plan
        state.phase = WorkflowPhase.PLAN

        self._workflows[workflow_id] = state
        return state

    async def approve_plan(self, workflow_id: str) -> WorkflowState:
        state = self._workflows[workflow_id]

        if state.phase != WorkflowPhase.PLAN:
            raise ValueError(
                f"Cannot approve plan in phase '{state.phase.value}'. "
                f"Expected phase: 'plan'"
            )

        state.phase = WorkflowPhase.EXECUTE

        # Build crew with plan parameters
        region = ", ".join(state.plan.geographical_scope) if state.plan.geographical_scope else "startup ecosystem"
        crew = self._crew or SimpleMarketCrew(region_context=region)

        result = crew.analyze_market(
            search_terms=state.plan.search_terms,
            geographical_scope=state.plan.geographical_scope,
            user_message=self._build_directed_message(state)
        )

        state.results = result
        state.phase = WorkflowPhase.COMPLETED

        self._workflows[workflow_id] = state
        return state

    async def reject_plan(self, workflow_id: str) -> WorkflowState:
        state = self._workflows[workflow_id]
        state.phase = WorkflowPhase.CANCELLED
        self._workflows[workflow_id] = state
        return state

    async def get_state(self, workflow_id: str) -> WorkflowState:
        if workflow_id not in self._workflows:
            raise KeyError(f"Workflow '{workflow_id}' not found")
        return self._workflows[workflow_id]

    def _build_directed_message(self, state: WorkflowState) -> str:
        """Build a focused user message from the original + clarification answers."""
        parts = [state.user_message]

        if state.user_answers:
            parts.append("\nAdditional context from user:")
            for key, value in state.user_answers.items():
                if key != "startup_selection":
                    parts.append(f"- {value}")

        if state.plan and state.plan.focus_areas:
            parts.append(f"\nFocus areas: {', '.join(state.plan.focus_areas)}")

        return "\n".join(parts)

    async def _generate_questions(
        self,
        user_message: str,
        existing_startups: List[StartupContext]
    ) -> List[ClarifyingQuestion]:
        """Use Haiku to generate targeted clarifying questions."""

        startup_context = ""
        if existing_startups:
            names = [f"- {s.name}: {s.description}" for s in existing_startups]
            startup_context = (
                f"\n\nThe user has previously worked on these startup ideas:\n"
                + "\n".join(names)
                + "\n\nInclude a question asking which startup they're working on, "
                "or if this is a new idea."
            )

        prompt = f"""Analyze this user message and generate 2-3 clarifying questions that will help focus a market research effort. The questions should help narrow down the target market, customer segment, geography, or specific angle of research.

User message: "{user_message}"
{startup_context}

Respond with valid JSON only, no other text. Format:
[
  {{"question": "...", "context": "...why this matters..."}},
  {{"question": "...", "context": "..."}}
]"""

        try:
            response = self._llm.call([
                {"role": "system", "content": "You generate focused clarifying questions for startup market research. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ])

            # Parse LLM response
            response_text = str(response) if not isinstance(response, str) else response
            # Strip markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]
            questions_data = json.loads(response_text.strip())

            return [
                ClarifyingQuestion(
                    question=q["question"],
                    context=q.get("context", "")
                )
                for q in questions_data
            ]
        except Exception as e:
            logger.warning(f"LLM question generation failed: {e}. Using fallback.")
            return self._fallback_questions(existing_startups)

    def _fallback_questions(
        self, existing_startups: List[StartupContext]
    ) -> List[ClarifyingQuestion]:
        """Fallback questions if LLM call fails."""
        questions = []

        if existing_startups:
            names = ", ".join(s.name for s in existing_startups)
            questions.append(ClarifyingQuestion(
                question=f"Are you continuing work on an existing idea ({names}), or starting something new?",
                context="Helps retrieve relevant past research context."
            ))

        questions.extend([
            ClarifyingQuestion(
                question="What customer segment are you targeting (B2B, B2C, or both)?",
                context="Determines market sizing approach and competitive landscape."
            ),
            ClarifyingQuestion(
                question="Is there a specific geography you want to focus on?",
                context="Scopes the research to relevant local resources and regulations."
            ),
        ])
        return questions

    async def _generate_plan(
        self,
        user_message: str,
        answers: Dict[str, str],
        startup: Optional[StartupContext]
    ) -> ResearchPlan:
        """Use Haiku to generate a structured research plan."""

        answers_text = "\n".join(f"- {v}" for k, v in answers.items() if k != "startup_selection")
        startup_text = ""
        if startup:
            startup_text = f"\nExisting startup context: {startup.name} - {startup.description} (industry: {startup.industry})"

        prompt = f"""Based on this user request and their answers to clarifying questions, generate a focused market research plan.

User request: "{user_message}"
{startup_text}

User's clarification answers:
{answers_text}

Respond with valid JSON only, no other text. Format:
{{
  "title": "Brief descriptive title for this research",
  "search_terms": ["term1", "term2", "term3"],
  "geographical_scope": ["region1"],
  "focus_areas": ["specific area to investigate 1", "specific area 2"],
  "steps": [
    {{"name": "Step name", "description": "What this step investigates", "agent_role": "Market Research Specialist", "estimated_duration": "~60 seconds"}},
    {{"name": "Step name", "description": "...", "agent_role": "Market Trend Analyst", "estimated_duration": "~60 seconds"}},
    {{"name": "Step name", "description": "...", "agent_role": "Opportunity Scout", "estimated_duration": "~60 seconds"}},
    {{"name": "Step name", "description": "...", "agent_role": "Market Analysis Validator", "estimated_duration": "~45 seconds"}}
  ]
}}"""

        try:
            response = self._llm.call([
                {"role": "system", "content": "You generate focused research plans for startup market analysis. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ])

            response_text = str(response) if not isinstance(response, str) else response
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]
            plan_data = json.loads(response_text.strip())

            return ResearchPlan(
                title=plan_data["title"],
                search_terms=plan_data.get("search_terms", []),
                geographical_scope=plan_data.get("geographical_scope", []),
                focus_areas=plan_data.get("focus_areas", []),
                steps=[
                    ResearchPlanStep(
                        name=s["name"],
                        description=s["description"],
                        agent_role=s.get("agent_role", ""),
                        estimated_duration=s.get("estimated_duration")
                    )
                    for s in plan_data.get("steps", [])
                ],
                estimated_duration="~4 minutes",
                estimated_cost="~50k tokens"
            )
        except Exception as e:
            logger.warning(f"LLM plan generation failed: {e}. Using fallback.")
            return self._fallback_plan(user_message, answers)

    def _fallback_plan(
        self, user_message: str, answers: Dict[str, str]
    ) -> ResearchPlan:
        """Fallback plan if LLM call fails."""
        # Extract basic terms from the message
        stop_words = {"i", "want", "to", "build", "a", "an", "the", "my", "for",
                      "in", "about", "need", "help", "with", "me", "am", "is", "are"}
        words = user_message.lower().split()
        terms = [w for w in words if w not in stop_words and len(w) > 2][:5]

        return ResearchPlan(
            title=f"Market Analysis: {user_message[:60]}",
            search_terms=terms or ["startup"],
            geographical_scope=[],
            focus_areas=[],
            steps=[
                ResearchPlanStep("Market Size Research", "Analyze TAM/SAM, growth rates, demographics", "Market Research Specialist", "~60 seconds"),
                ResearchPlanStep("Trend Analysis", "Identify emerging trends and market shifts", "Market Trend Analyst", "~60 seconds"),
                ResearchPlanStep("Opportunity Identification", "Find market gaps and entry strategies", "Opportunity Scout", "~60 seconds"),
                ResearchPlanStep("Validation & Synthesis", "Cross-verify findings, prioritize recommendations", "Market Analysis Validator", "~45 seconds"),
            ],
            estimated_duration="~4 minutes",
            estimated_cost="~50k tokens"
        )
