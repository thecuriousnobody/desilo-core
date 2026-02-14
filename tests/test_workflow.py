"""Tests for the deterministic workflow orchestrator.

All tests mock LLM calls and crew execution — no API keys needed.

Usage:
    pytest tests/test_workflow.py -v
"""

import json
import asyncio
import tempfile
import shutil
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from desilo_core.contracts.workflow import (
    WorkflowPhase, StartupContext, ClarifyingQuestion,
    ResearchPlan, ResearchPlanStep, WorkflowState,
    StartupContextStore,
)
from desilo_core.workflow.orchestrator import DefaultOrchestrator
from desilo_core.workflow.context_store import FileContextStore


# --- Fixtures ---

class InMemoryContextStore(StartupContextStore):
    """Test context store backed by a dict."""

    def __init__(self, startups=None):
        self._startups = {s.id: s for s in (startups or [])}

    async def get_user_startups(self, user_id):
        return [s for s in self._startups.values() if s.user_id == user_id]

    async def get_startup_by_id(self, startup_id):
        return self._startups.get(startup_id)

    async def save_startup(self, context):
        self._startups[context.id] = context
        return context.id


MOCK_QUESTIONS_JSON = json.dumps([
    {"question": "Are you targeting B2B or B2C?", "context": "Determines market sizing"},
    {"question": "What geography?", "context": "Scopes local resources"},
])

MOCK_PLAN_JSON = json.dumps({
    "title": "AI Market Analysis - US",
    "search_terms": ["artificial intelligence", "AI startups"],
    "geographical_scope": ["United States"],
    "focus_areas": ["B2B enterprise AI", "regulatory landscape"],
    "steps": [
        {"name": "Market Size", "description": "Analyze TAM/SAM", "agent_role": "Market Research Specialist", "estimated_duration": "~60s"},
        {"name": "Trends", "description": "Identify trends", "agent_role": "Market Trend Analyst", "estimated_duration": "~60s"},
        {"name": "Opportunities", "description": "Find gaps", "agent_role": "Opportunity Scout", "estimated_duration": "~60s"},
        {"name": "Validation", "description": "Synthesize", "agent_role": "Market Analysis Validator", "estimated_duration": "~45s"},
    ]
})

MOCK_CREW_RESULT = {
    "status": "success",
    "data": {"raw_output": "mock analysis", "market_size": "$10B"},
    "confidence": 0.8,
    "sources": [],
}


def make_mock_llm():
    """Create a mock LLM that returns questions then plan."""
    llm = MagicMock()
    llm.call = MagicMock(side_effect=[MOCK_QUESTIONS_JSON, MOCK_PLAN_JSON])
    return llm


def make_startup(id, user_id, name, description="test", industry="tech"):
    return StartupContext(
        id=id, user_id=user_id, name=name,
        description=description, industry=industry,
        search_terms=[name.lower()], geographical_scope=["US"],
    )


# --- Contract Tests ---

class TestWorkflowDataclasses:
    """Verify workflow data structures."""

    def test_workflow_phase_values(self):
        assert WorkflowPhase.CLARIFY.value == "clarify"
        assert WorkflowPhase.PLAN.value == "plan"
        assert WorkflowPhase.EXECUTE.value == "execute"
        assert WorkflowPhase.COMPLETED.value == "completed"
        assert WorkflowPhase.CANCELLED.value == "cancelled"

    def test_startup_context_creation(self):
        ctx = StartupContext(id="1", user_id="u1", name="Test", description="desc")
        assert ctx.id == "1"
        assert ctx.industry is None
        assert ctx.search_terms is None

    def test_clarifying_question(self):
        q = ClarifyingQuestion(question="What market?", context="Scoping")
        assert q.question == "What market?"

    def test_research_plan_step(self):
        step = ResearchPlanStep("Step 1", "Do research", "Analyst")
        assert step.estimated_duration is None

    def test_research_plan(self):
        plan = ResearchPlan(
            title="Test", steps=[], search_terms=["ai"],
            geographical_scope=["US"], focus_areas=["B2B"]
        )
        assert plan.estimated_cost is None


# --- Orchestrator State Machine Tests ---

class TestOrchestratorFlow:
    """Test the full clarify -> plan -> execute flow."""

    @pytest.fixture
    def orchestrator_no_startups(self):
        store = InMemoryContextStore()
        llm = make_mock_llm()
        return DefaultOrchestrator(context_store=store, llm=llm)

    @pytest.fixture
    def orchestrator_with_startups(self):
        startups = [
            make_startup("s1", "user_1", "Fintech App", "payments platform", "fintech"),
            make_startup("s2", "user_1", "AI Tool", "writing assistant", "ai"),
        ]
        store = InMemoryContextStore(startups)
        llm = make_mock_llm()
        return DefaultOrchestrator(context_store=store, llm=llm)

    def test_start_returns_clarify_phase(self, orchestrator_no_startups):
        state = asyncio.run(orchestrator_no_startups.start("user_1", "explore AI market"))
        assert state.phase == WorkflowPhase.CLARIFY
        assert len(state.clarifying_questions) == 2
        assert state.available_startups is None
        assert state.user_message == "explore AI market"

    def test_start_with_existing_startups(self, orchestrator_with_startups):
        state = asyncio.run(orchestrator_with_startups.start("user_1", "explore AI market"))
        assert state.phase == WorkflowPhase.CLARIFY
        assert state.available_startups is not None
        assert len(state.available_startups) == 2

    def test_answer_questions_returns_plan_phase(self, orchestrator_no_startups):
        state = asyncio.run(orchestrator_no_startups.start("user_1", "explore AI market"))
        state = asyncio.run(orchestrator_no_startups.answer_questions(
            state.workflow_id, {"q1": "B2B", "q2": "US market"}
        ))
        assert state.phase == WorkflowPhase.PLAN
        assert state.plan is not None
        assert state.plan.title == "AI Market Analysis - US"
        assert len(state.plan.steps) == 4
        assert state.plan.search_terms == ["artificial intelligence", "AI startups"]

    def test_answer_with_startup_selection(self, orchestrator_with_startups):
        state = asyncio.run(orchestrator_with_startups.start("user_1", "continue my work"))
        state = asyncio.run(orchestrator_with_startups.answer_questions(
            state.workflow_id, {"startup_selection": "s1", "q1": "B2B"}
        ))
        assert state.phase == WorkflowPhase.PLAN
        assert state.startup_context is not None
        assert state.startup_context.name == "Fintech App"

    @patch("desilo_core.workflow.orchestrator.SimpleMarketCrew")
    def test_approve_executes_and_completes(self, mock_crew_cls, orchestrator_no_startups):
        mock_crew = MagicMock()
        mock_crew.analyze_market.return_value = MOCK_CREW_RESULT
        mock_crew_cls.return_value = mock_crew

        state = asyncio.run(orchestrator_no_startups.start("user_1", "AI market"))
        state = asyncio.run(orchestrator_no_startups.answer_questions(
            state.workflow_id, {"q1": "B2B"}
        ))
        state = asyncio.run(orchestrator_no_startups.approve_plan(state.workflow_id))

        assert state.phase == WorkflowPhase.COMPLETED
        assert state.results == MOCK_CREW_RESULT
        mock_crew.analyze_market.assert_called_once()

    def test_reject_cancels(self, orchestrator_no_startups):
        state = asyncio.run(orchestrator_no_startups.start("user_1", "AI market"))
        state = asyncio.run(orchestrator_no_startups.answer_questions(
            state.workflow_id, {"q1": "B2B"}
        ))
        state = asyncio.run(orchestrator_no_startups.reject_plan(state.workflow_id))
        assert state.phase == WorkflowPhase.CANCELLED

    def test_get_state(self, orchestrator_no_startups):
        state = asyncio.run(orchestrator_no_startups.start("user_1", "test"))
        retrieved = asyncio.run(orchestrator_no_startups.get_state(state.workflow_id))
        assert retrieved.workflow_id == state.workflow_id

    def test_get_state_unknown_id_raises(self, orchestrator_no_startups):
        with pytest.raises(KeyError):
            asyncio.run(orchestrator_no_startups.get_state("nonexistent"))


# --- Phase Validation Tests ---

class TestPhaseValidation:
    """Test that methods reject calls in wrong phases."""

    def test_answer_in_plan_phase_raises(self):
        store = InMemoryContextStore()
        llm = make_mock_llm()
        orch = DefaultOrchestrator(context_store=store, llm=llm)

        state = asyncio.run(orch.start("user_1", "test"))
        asyncio.run(orch.answer_questions(state.workflow_id, {"q1": "answer"}))
        # Now in PLAN phase, answering again should fail
        with pytest.raises(ValueError, match="Cannot answer questions"):
            asyncio.run(orch.answer_questions(state.workflow_id, {"q1": "again"}))

    @patch("desilo_core.workflow.orchestrator.SimpleMarketCrew")
    def test_approve_in_clarify_phase_raises(self, mock_crew_cls):
        store = InMemoryContextStore()
        llm = make_mock_llm()
        orch = DefaultOrchestrator(context_store=store, llm=llm)

        state = asyncio.run(orch.start("user_1", "test"))
        with pytest.raises(ValueError, match="Cannot approve plan"):
            asyncio.run(orch.approve_plan(state.workflow_id))


# --- Fallback Tests ---

class TestFallbacks:
    """Test fallback behavior when LLM calls fail."""

    def test_question_generation_fallback(self):
        store = InMemoryContextStore()
        llm = MagicMock()
        llm.call = MagicMock(side_effect=[Exception("LLM down"), MOCK_PLAN_JSON])
        orch = DefaultOrchestrator(context_store=store, llm=llm)

        state = asyncio.run(orch.start("user_1", "explore market"))
        assert state.phase == WorkflowPhase.CLARIFY
        assert len(state.clarifying_questions) >= 2  # Fallback provides questions

    def test_plan_generation_fallback(self):
        store = InMemoryContextStore()
        llm = MagicMock()
        llm.call = MagicMock(side_effect=[MOCK_QUESTIONS_JSON, Exception("LLM down")])
        orch = DefaultOrchestrator(context_store=store, llm=llm)

        state = asyncio.run(orch.start("user_1", "AI startup market"))
        state = asyncio.run(orch.answer_questions(state.workflow_id, {"q1": "B2B"}))
        assert state.phase == WorkflowPhase.PLAN
        assert state.plan is not None
        assert len(state.plan.steps) == 4  # Fallback plan


# --- FileContextStore Tests ---

class TestFileContextStore:
    """Test filesystem-based context store."""

    @pytest.fixture
    def store(self, tmp_path):
        return FileContextStore(str(tmp_path / "startups"))

    def test_save_and_retrieve(self, store):
        ctx = make_startup("s1", "user_1", "Test Startup")
        asyncio.run(store.save_startup(ctx))

        results = asyncio.run(store.get_user_startups("user_1"))
        assert len(results) == 1
        assert results[0].name == "Test Startup"

    def test_get_by_id(self, store):
        ctx = make_startup("s1", "user_1", "Test Startup")
        asyncio.run(store.save_startup(ctx))

        result = asyncio.run(store.get_startup_by_id("s1"))
        assert result is not None
        assert result.id == "s1"

    def test_get_nonexistent_user(self, store):
        results = asyncio.run(store.get_user_startups("nobody"))
        assert results == []

    def test_get_nonexistent_id(self, store):
        result = asyncio.run(store.get_startup_by_id("nope"))
        assert result is None

    def test_multiple_startups_per_user(self, store):
        asyncio.run(store.save_startup(make_startup("s1", "user_1", "First")))
        asyncio.run(store.save_startup(make_startup("s2", "user_1", "Second")))

        results = asyncio.run(store.get_user_startups("user_1"))
        assert len(results) == 2
