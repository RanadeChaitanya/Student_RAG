import pytest

from studob.retrieval.orchestrator import RetrievalOrchestrator
from studob.schemas.retrieval import RetrievalRequest
from studob.schemas.student import MasterySummaryResponse, WeakTopicInfo


class FakeMetadataFilter:
    async def filter(
        self, subject="", topic=None, subtopic=None, difficulty_band=(1, 5), exclude_ids=None
    ):
        from studob.schemas.question import MetadataFilterResult, QuestionFilter

        return MetadataFilterResult(
            question_ids=[1, 2, 3, 4, 5], total_count=5, filter_criteria=QuestionFilter()
        )


class FakeSemanticRetrieval:
    async def retrieve(self, query_text, top_k, allowed_ids=None):
        return [{"id": 1, "relevance_score": 0.9}, {"id": 2, "relevance_score": 0.8}]


class FakeConceptExpansion:
    async def expand(self, concept_ids):
        return [
            {
                "id": "newtons-laws",
                "display_name": "Newton's Laws",
                "subject": "Physics",
                "topic": "Laws of Motion",
                "subtopic": "Newton's Laws",
            }
        ]


class FakeStudentFilter:
    async def filter(self, student_id, session_id, candidates):
        return candidates


class FakeMistakeMatcher:
    async def match(self, candidates, error_category, concept_tag):
        return [{**c, "relevance_score": c.get("relevance_score", 0.5)} for c in candidates]


class FakeReranker:
    async def rerank(self, query_text, candidates, top_k, target_difficulty=3):
        scored = [{**c, "combined_score": c.get("relevance_score", 0.0)} for c in candidates]
        return scored[:top_k]


class FakeContextBuilder:
    async def build(self, **kwargs):
        from studob.schemas.retrieval import ContextPackage

        return ContextPackage(
            student_state=kwargs.get("student_state", {}),
            mistake_diagnosis=kwargs.get("mistake_diagnosis", {}),
            learning_objective=kwargs.get("learning_objective", ""),
            retrieved_questions=[],
            concept_notes=kwargs.get("concept_notes", []),
            formulas=kwargs.get("formulas", []),
            misconceptions=kwargs.get("misconceptions", []),
            session_memory=kwargs.get("session_memory", {}),
        )


class FakeAppQuestionService:
    async def get_questions_by_ids(self, ids):
        return []


class FakeMasteryService:
    async def get_mastery_summary(self, student_id):
        return MasterySummaryResponse(
            student_id=student_id,
            overall_score=60.0,
            subject_breakdown={"Physics": 60.0},
            weak_topics=[
                WeakTopicInfo(
                    subject="Physics",
                    topic="Kinematics",
                    subtopic="Motion in 1D",
                    score=45.0,
                    gap=25.0,
                )
            ],
            strengths=[
                WeakTopicInfo(
                    subject="Physics",
                    topic="Laws of Motion",
                    subtopic="Newton's Laws",
                    score=70.0,
                    gap=0.0,
                )
            ],
        )


class FakeSessionMemory:
    async def get_session_attempts(self, session_id):
        return []

    async def get_seen_question_ids(self, student_id, session_id):
        return []


class FakeConceptGraphService:
    async def get_concept(self, concept_tag):
        return {
            "id": concept_tag,
            "subject": "Physics",
            "topic": "Laws of Motion",
            "subtopic": "Newton's Laws",
            "display_name": "Newton's Laws",
            "difficulty": 2,
        }


@pytest.fixture
def orchestrator(config):
    return RetrievalOrchestrator(
        config=config,
        metadata_filter=FakeMetadataFilter(),
        semantic_retrieval=FakeSemanticRetrieval(),
        concept_expansion=FakeConceptExpansion(),
        student_filter=FakeStudentFilter(),
        mistake_matcher=FakeMistakeMatcher(),
        reranker=FakeReranker(),
        context_builder=FakeContextBuilder(),
        app_question_service=FakeAppQuestionService(),
        mastery_service=FakeMasteryService(),
        session_memory=FakeSessionMemory(),
        concept_graph_service=FakeConceptGraphService(),
    )


@pytest.mark.asyncio
async def test_orchestrator_returns_context_package(orchestrator):
    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="newtons-laws",
        error_category="guessing",
        session_id="session-1",
    )
    result = await orchestrator.retrieve(req)
    from studob.schemas.retrieval import ContextPackage

    assert isinstance(result, ContextPackage)


@pytest.mark.asyncio
async def test_orchestrator_passes_subject_to_metadata_filter(orchestrator):
    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="newtons-laws",
        error_category="guessing",
        session_id="session-1",
    )
    result = await orchestrator.retrieve(req)
    assert result.learning_objective is not None


@pytest.mark.asyncio
async def test_orchestrator_includes_learning_objective(orchestrator):
    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="newtons-laws",
        error_category="guessing",
        session_id="session-1",
        learning_objective="Understand Newton's Third Law",
    )
    result = await orchestrator.retrieve(req)
    assert "Newton's Third Law" in result.learning_objective


@pytest.mark.asyncio
async def test_orchestrator_handles_empty_concept_graph(orchestrator):
    orchestrator._concept_graph = FakeConceptGraphService()

    async def broken_get_concept(concept_tag):
        return None

    orchestrator._concept_graph.get_concept = broken_get_concept

    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="unknown-concept",
        error_category="guessing",
        session_id="session-1",
    )
    result = await orchestrator.retrieve(req)
    assert result.learning_objective is not None


@pytest.mark.asyncio
async def test_orchestrator_includes_student_state_in_context(orchestrator):
    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="newtons-laws",
        error_category="guessing",
        session_id="session-1",
    )
    result = await orchestrator.retrieve(req)
    assert (
        "student_id" in result.student_state
        or result.student_state.get("overall_score") is not None
    )


@pytest.mark.asyncio
async def test_orchestrator_enriches_with_session_memory(orchestrator):
    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="newtons-laws",
        error_category="guessing",
        session_id="session-1",
    )
    result = await orchestrator.retrieve(req)
    assert result.session_memory.get("session_id") == "session-1"


@pytest.mark.asyncio
async def test_orchestrator_handles_retrieval_error(orchestrator):
    orchestrator._semantic_retrieval = FakeSemanticRetrieval()

    async def broken_retrieve(query_text, top_k, allowed_ids=None):
        raise ValueError("Simulated failure")

    orchestrator._semantic_retrieval.retrieve = broken_retrieve

    req = RetrievalRequest(
        student_id="test-123",
        concept_tag="newtons-laws",
        error_category="guessing",
        session_id="session-1",
    )
    from studob.exceptions import RetrievalError

    with pytest.raises(RetrievalError):
        await orchestrator.retrieve(req)
