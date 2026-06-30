import logging
import time

from studob.config.loader import Settings
from studob.exceptions import RetrievalError
from studob.graph.service import ConceptGraphService
from studob.logging_setup import get_logger
from studob.question_bank.app_questions import AppQuestionService
from studob.retrieval.concept_expansion import ConceptExpansionModule
from studob.retrieval.context_builder import ContextBuilder
from studob.retrieval.metadata_filter import MetadataFilterModule
from studob.retrieval.mistake_matcher import MistakePatternMatcher
from studob.retrieval.reranker import CrossEncoderReranker
from studob.retrieval.semantic import SemanticRetrievalModule
from studob.retrieval.student_filter import StudentFilterModule
from studob.schemas.retrieval import ContextPackage, RetrievalRequest
from studob.student.mastery import MasteryService
from studob.student.session_memory import SessionMemoryService

logger = get_logger("retrieval.orchestrator")


class RetrievalOrchestrator:
    def __init__(
        self,
        config: Settings,
        metadata_filter: MetadataFilterModule,
        semantic_retrieval: SemanticRetrievalModule,
        concept_expansion: ConceptExpansionModule,
        student_filter: StudentFilterModule,
        mistake_matcher: MistakePatternMatcher,
        reranker: CrossEncoderReranker,
        context_builder: ContextBuilder,
        app_question_service: AppQuestionService,
        mastery_service: MasteryService,
        session_memory: SessionMemoryService,
        concept_graph_service: ConceptGraphService,
        logger: logging.Logger = logger,
    ) -> None:
        self._config = config
        self._metadata_filter = metadata_filter
        self._semantic_retrieval = semantic_retrieval
        self._concept_expansion = concept_expansion
        self._student_filter = student_filter
        self._mistake_matcher = mistake_matcher
        self._reranker = reranker
        self._context_builder = context_builder
        self._app_question_service = app_question_service
        self._mastery_service = mastery_service
        self._session_memory = session_memory
        self._concept_graph = concept_graph_service
        self._logger = logger

    async def retrieve(self, request: RetrievalRequest) -> ContextPackage:
        overall_start = time.perf_counter()
        self._logger.info(
            "Retrieval request started",
            extra={
                "student_id": request.student_id,
                "concept_tag": request.concept_tag,
                "error_category": request.error_category,
                "session_id": request.session_id,
            },
        )
        try:
            student_state = await self._load_student_state(request.student_id)

            concept_info = await self._get_concept_info(request.concept_tag)
            expanded = []
            if self._config.retrieval.enable_concept_expansion:
                expanded = await self._concept_expansion.expand([request.concept_tag])
                self._logger.info(
                    "Concept expansion yielded concepts", extra={"count": len(expanded)}
                )

            subject = concept_info.get("subject", "") if concept_info else ""
            topic = concept_info.get("topic") if concept_info else None
            subtopic = concept_info.get("subtopic") if concept_info else None

            difficulty_low, difficulty_high = 1, 5
            for wt in student_state.weak_topics:
                if request.concept_tag.lower() in wt.subtopic.lower():
                    score = wt.score
                    if score < 30:
                        difficulty_low, difficulty_high = 1, 2
                    elif score < 50:
                        difficulty_low, difficulty_high = 1, 3
                    elif score < 70:
                        difficulty_low, difficulty_high = 2, 4
                    else:
                        difficulty_low, difficulty_high = 3, 5
                    break

            seen_ids = await self._session_memory.get_seen_question_ids(
                request.student_id, request.session_id
            )

            meta_result = await self._metadata_filter.filter(
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                difficulty_band=(difficulty_low, difficulty_high),
                exclude_ids=seen_ids if seen_ids else None,
            )
            allowed_ids = (
                {str(qid) for qid in meta_result.question_ids} if meta_result.question_ids else None
            )

            expanded_names = [
                n.get("display_name", n.get("id", ""))
                for n in expanded
                if n.get("id") != request.concept_tag
            ]
            learning_objective = (
                request.learning_objective or f"{request.error_category} on {request.concept_tag}"
            )
            if expanded_names:
                related = ", ".join(expanded_names[:3])
                learning_objective = f"{learning_objective} related to: {related}"

            top_k_before = self._config.retrieval.top_k_before_reranking
            semantic_results = await self._semantic_retrieval.retrieve(
                query_text=learning_objective,
                top_k=top_k_before,
                allowed_ids=allowed_ids,
            )

            if self._config.retrieval.enable_student_filter:
                filtered = await self._student_filter.filter(
                    student_id=request.student_id,
                    session_id=request.session_id,
                    candidates=semantic_results,
                )
            else:
                filtered = semantic_results

            if self._config.retrieval.enable_mistake_matching:
                matched = await self._mistake_matcher.match(
                    candidates=filtered,
                    error_category=request.error_category,
                    concept_tag=request.concept_tag,
                )
            else:
                matched = [
                    {**c, "relevance_score": c.get("relevance_score", 0.5)} for c in filtered
                ]

            target_difficulty = (difficulty_low + difficulty_high) // 2
            top_k_after = self._config.retrieval.top_k_after_reranking
            if self._config.retrieval.enable_reranking:
                reranked = await self._reranker.rerank(
                    query_text=learning_objective,
                    candidates=matched,
                    top_k=top_k_after,
                    target_difficulty=target_difficulty,
                )
            else:
                matched.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
                reranked = matched[:top_k_after]

            question_ids = [
                str(q.get("id") or q.get("question_id"))
                for q in reranked
                if q.get("id") or q.get("question_id")
            ]
            full_questions = await self._app_question_service.get_questions_by_ids(question_ids)
            full_questions_dict = {str(q.id): q for q in full_questions}

            enriched = []
            for q in reranked:
                qid = str(q.get("id") or q.get("question_id"))
                full = full_questions_dict.get(qid)
                if full:
                    enriched.append(
                        {
                            "id": full.id,
                            "subject": full.subject,
                            "topic": full.topic,
                            "subtopic": full.subtopic,
                            "difficulty": full.difficulty,
                            "question_text": full.question_text,
                            "options": full.options,
                            "explanation": full.explanation,
                            "source": full.source,
                            "combined_score": q.get("combined_score")
                            or q.get("relevance_score", 0.0),
                            "relevance_score": q.get("relevance_score", 0.0),
                        }
                    )

            session_mem = await self._session_memory.get_session_attempts(request.session_id)
            session_memory_dict = {
                "session_id": request.session_id,
                "attempts_count": len(session_mem),
                "recent_attempts": [
                    {
                        "question_id": a.question_id,
                        "is_correct": a.is_correct,
                    }
                    for a in session_mem[-5:]
                ],
            }

            context = await self._context_builder.build(
                student_state=student_state.model_dump()
                if hasattr(student_state, "model_dump")
                else student_state,
                mistake_diagnosis={
                    "error_category": request.error_category,
                    "concept_tag": request.concept_tag,
                },
                learning_objective=learning_objective,
                retrieved_questions=enriched,
                concept_notes=[],
                formulas=[],
                misconceptions=[],
                session_memory=session_memory_dict,
            )

            overall_elapsed = int((time.perf_counter() - overall_start) * 1000)
            self._logger.info(
                "Retrieval request completed",
                extra={
                    "student_id": request.student_id,
                    "session_id": request.session_id,
                    "result_count": len(context.retrieved_questions),
                    "duration_ms": overall_elapsed,
                },
            )
            return context

        except RetrievalError:
            raise
        except Exception as e:
            overall_elapsed = int((time.perf_counter() - overall_start) * 1000)
            self._logger.error(
                "Retrieval request failed",
                extra={"error": str(e), "duration_ms": overall_elapsed},
            )
            raise RetrievalError(f"Retrieval orchestration failed: {e}") from e

    async def _get_concept_info(self, concept_tag: str) -> dict | None:
        try:
            return await self._concept_graph.get_concept(concept_tag)
        except Exception:
            self._logger.warning(
                "Could not get concept info from graph",
                extra={"concept_tag": concept_tag},
            )
            return None

    async def _load_student_state(self, student_id: str):
        start = time.perf_counter()
        try:
            summary = await self._mastery_service.get_mastery_summary(student_id)
            elapsed = int((time.perf_counter() - start) * 1000)
            self._logger.info(
                "Student state loaded",
                extra={"student_id": student_id, "duration_ms": elapsed},
            )
            return summary
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            self._logger.warning(
                "Failed to load student state, using defaults",
                extra={"student_id": student_id, "error": str(e), "duration_ms": elapsed},
            )
            from studob.schemas.student import MasterySummaryResponse

            return MasterySummaryResponse(
                student_id=student_id,
                overall_score=0.0,
                subject_breakdown={},
                weak_topics=[],
                strengths=[],
            )

    async def health_check(self) -> dict:
        status = {}
        checks = {
            "metadata_filter": self._metadata_filter,
            "semantic_retrieval": self._semantic_retrieval,
            "concept_expansion": self._concept_expansion,
            "student_filter": self._student_filter,
            "mistake_matcher": self._mistake_matcher,
            "reranker": self._reranker,
            "context_builder": self._context_builder,
            "app_question_service": self._app_question_service,
            "mastery_service": self._mastery_service,
            "session_memory": self._session_memory,
        }
        overall_healthy = True
        for name, module in checks.items():
            try:
                if module is not None:
                    status[name] = "available"
                else:
                    status[name] = "unavailable"
                    overall_healthy = False
            except Exception:
                status[name] = "error"
                overall_healthy = False
        return {"healthy": overall_healthy, "modules": status}
