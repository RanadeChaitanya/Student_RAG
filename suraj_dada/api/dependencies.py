from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from suraj_dada.analytics import AnalyticsService
from suraj_dada.analytics.mastery_trends import MasteryTrendService
from suraj_dada.analytics.mistake_patterns import MistakePatternService
from suraj_dada.analytics.session_reports import SessionReportService
from suraj_dada.assessment import AnswerEvaluator, AnswerTagger, AssessmentEngine
from suraj_dada.config.loader import Settings, get_config
from suraj_dada.database.engine import DatabaseEngine
from suraj_dada.diagnosis import (
    ConceptTagger,
    DiagnosisEngine,
    ErrorTypeRegistry,
    RootCauseClassifier,
)
from suraj_dada.embeddings import EmbeddingGenerator, EmbeddingService, VectorStoreService
from suraj_dada.graph import ConceptGraphService
from suraj_dada.graph.store import ConceptGraphStore
from suraj_dada.llm import LlmClient, LlmPracticeGenerator, MockPracticeGenerator, OutputParser
from suraj_dada.question_bank import AppQuestionService, MetadataFilterService, TestQuestionService
from suraj_dada.retrieval import (
    ConceptExpansionModule,
    ContextBuilder,
    CrossEncoderReranker,
    MetadataFilterModule,
    MistakePatternMatcher,
    RetrievalOrchestrator,
    SemanticRetrievalModule,
    StudentFilterModule,
)
from suraj_dada.student import MasteryService, SessionMemoryService, StudentProfileService


class AppContext:
    def __init__(self):
        self.db_engine: DatabaseEngine | None = None
        self.student_profile: StudentProfileService | None = None
        self.mastery: MasteryService | None = None
        self.session_memory: SessionMemoryService | None = None
        self.app_questions: AppQuestionService | None = None
        self.test_questions: TestQuestionService | None = None
        self.metadata_filter: MetadataFilterService | None = None
        self.embedding: EmbeddingService | None = None
        self.concept_graph: ConceptGraphService | None = None
        self.diagnosis: DiagnosisEngine | None = None
        self.retrieval: RetrievalOrchestrator | None = None
        self.practice_generator: Optional = None
        self.assessment: AssessmentEngine | None = None
        self.analytics: AnalyticsService | None = None

    async def initialize(self, settings: Settings) -> None:
        self.db_engine = DatabaseEngine(
            url=settings.database.rdbms.url,
            echo=settings.database.rdbms.echo,
            pool_size=settings.database.rdbms.pool_size,
            max_overflow=settings.database.rdbms.max_overflow,
        )
        await self.db_engine.init_db()
        session_factory = self.db_engine.get_session_factory()

        self.student_profile = StudentProfileService(session_factory)
        self.mastery = MasteryService(session_factory, settings)
        self.session_memory = SessionMemoryService(session_factory)

        self.app_questions = AppQuestionService(session_factory)
        self.test_questions = TestQuestionService(session_factory)
        self.metadata_filter = MetadataFilterService(session_factory)

        embedding_generator = EmbeddingGenerator(settings.database.vector.dimension)
        vector_store = VectorStoreService(
            dimension=settings.database.vector.dimension,
            index_path=settings.database.vector.index_path,
        )
        self.embedding = EmbeddingService(embedding_generator, vector_store)

        concept_graph_store = ConceptGraphStore(settings.database.graph.data_path)
        self.concept_graph = ConceptGraphService(concept_graph_store, settings)

        error_type_registry = ErrorTypeRegistry()
        concept_tagger = ConceptTagger(self.app_questions)
        root_cause_classifier = RootCauseClassifier(settings)
        self.diagnosis = DiagnosisEngine(
            classifier=root_cause_classifier,
            tagger=concept_tagger,
            registry=error_type_registry,
            session_factory=session_factory,
            app_question_service=self.app_questions,
            test_question_service=self.test_questions,
        )

        metadata_filter_module = MetadataFilterModule(self.metadata_filter)
        semantic_retrieval = SemanticRetrievalModule(self.embedding)
        concept_expansion = ConceptExpansionModule(self.concept_graph)
        student_filter = StudentFilterModule(self.session_memory)
        mistake_matcher = MistakePatternMatcher()
        reranker = CrossEncoderReranker(settings)
        context_builder = ContextBuilder()
        self.retrieval = RetrievalOrchestrator(
            config=settings,
            metadata_filter=metadata_filter_module,
            semantic_retrieval=semantic_retrieval,
            concept_expansion=concept_expansion,
            student_filter=student_filter,
            mistake_matcher=mistake_matcher,
            reranker=reranker,
            context_builder=context_builder,
            app_question_service=self.app_questions,
            mastery_service=self.mastery,
            session_memory=self.session_memory,
        )

        output_parser = OutputParser()
        if settings.llm.provider == "mock":
            self.practice_generator = MockPracticeGenerator(config=settings)
        else:
            llm_client = LlmClient(settings)
            self.practice_generator = LlmPracticeGenerator(llm_client, output_parser, settings)

        answer_evaluator = AnswerEvaluator()
        answer_tagger = AnswerTagger()
        self.assessment = AssessmentEngine(
            session_factory=session_factory,
            test_question_service=self.test_questions,
            session_memory=self.session_memory,
            evaluator=answer_evaluator,
            tagger=answer_tagger,
            config=settings,
        )

        mastery_trends = MasteryTrendService(session_factory)
        mistake_patterns_analytics = MistakePatternService(session_factory)
        session_reports = SessionReportService(session_factory)
        self.analytics = AnalyticsService(
            mastery_trends=mastery_trends,
            mistake_patterns=mistake_patterns_analytics,
            session_reports=session_reports,
            mastery_service=self.mastery,
        )


async def get_settings() -> AsyncGenerator[Settings, None]:
    yield get_config()


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    context: AppContext = request.app.state.context
    async with context.db_engine.get_session() as session:
        yield session


async def get_student_profile_service(
    request: Request,
) -> AsyncGenerator[StudentProfileService, None]:
    yield request.app.state.context.student_profile


async def get_mastery_service(request: Request) -> AsyncGenerator[MasteryService, None]:
    yield request.app.state.context.mastery


async def get_session_memory_service(
    request: Request,
) -> AsyncGenerator[SessionMemoryService, None]:
    yield request.app.state.context.session_memory


async def get_app_question_service(request: Request) -> AsyncGenerator[AppQuestionService, None]:
    yield request.app.state.context.app_questions


async def get_test_question_service(request: Request) -> AsyncGenerator[TestQuestionService, None]:
    yield request.app.state.context.test_questions


async def get_metadata_filter_service(
    request: Request,
) -> AsyncGenerator[MetadataFilterService, None]:
    yield request.app.state.context.metadata_filter


async def get_embedding_service(request: Request) -> AsyncGenerator[EmbeddingService, None]:
    yield request.app.state.context.embedding


async def get_concept_graph_service(request: Request) -> AsyncGenerator[ConceptGraphService, None]:
    yield request.app.state.context.concept_graph


async def get_diagnosis_engine(request: Request) -> AsyncGenerator[DiagnosisEngine, None]:
    yield request.app.state.context.diagnosis


async def get_retrieval_orchestrator(
    request: Request,
) -> AsyncGenerator[RetrievalOrchestrator, None]:
    yield request.app.state.context.retrieval


async def get_practice_generator(request: Request) -> AsyncGenerator:
    yield request.app.state.context.practice_generator


async def get_assessment_engine(request: Request) -> AsyncGenerator[AssessmentEngine, None]:
    yield request.app.state.context.assessment


async def get_analytics_service(request: Request) -> AsyncGenerator[AnalyticsService, None]:
    yield request.app.state.context.analytics
