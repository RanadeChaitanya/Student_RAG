from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from suraj_dada.database.models import Attempt, MasteryScore, MistakeRecord
from suraj_dada.diagnosis.classifier import RootCauseClassifier
from suraj_dada.diagnosis.concept_tagger import ConceptTagger
from suraj_dada.diagnosis.error_types import ErrorTypeRegistry
from suraj_dada.exceptions import DiagnosisError
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.diagnosis import (
    ErrorCategory,
    MistakeDiagnosisRequest,
    MistakeDiagnosisResponse,
    MistakeRecordResponse,
)

_DIAGNOSIS_LOGGER = get_logger("diagnosis.engine")


class DiagnosisEngine:
    def __init__(
        self,
        classifier: RootCauseClassifier,
        tagger: ConceptTagger,
        registry: ErrorTypeRegistry,
        session_factory,
        app_question_service=None,
        test_question_service=None,
    ):
        self._classifier = classifier
        self._tagger = tagger
        self._registry = registry
        self._session_factory = session_factory
        self._app_q_service = app_question_service
        self._test_q_service = test_question_service
        self._logger = _DIAGNOSIS_LOGGER

    async def diagnose(
        self,
        request: MistakeDiagnosisRequest,
    ) -> MistakeDiagnosisResponse:
        student_context: dict[str, Any] = {
            "mastery_scores": [],
            "recent_mistakes": [],
            "avg_response_time": 30.0,
            "question_data": {},
            "_registry": self._registry,
        }

        try:
            await self._load_student_context(request, student_context)
        except Exception as exc:
            raise DiagnosisError(
                "Failed to load student context",
                details={"student_id": request.student_id, "error": str(exc)},
            ) from exc

        question_data = student_context["question_data"]
        student_context["avg_response_time"] = (
            await self._compute_avg_response_time(
                request.student_id,
            )
            or 30.0
        )

        try:
            response = await self._classifier.classify(request, student_context)
        except Exception as exc:
            raise DiagnosisError(
                "Classification failed",
                details={"student_id": request.student_id, "error": str(exc)},
            ) from exc

        try:
            qid_str = str(request.question_id)
            tags = await self._tagger.extract_concept_tags(qid_str)
            primary_tag = (
                tags[0]
                if tags
                else (question_data.get("subtopic") or question_data.get("topic", "general"))
            )
            response.concept_tag = primary_tag
        except Exception as exc:
            self._logger.warning(
                "Concept tagging failed, using fallback",
                extra={"question_id": request.question_id, "error": str(exc)},
            )
            response.concept_tag = question_data.get("subtopic") or question_data.get(
                "topic", "general"
            )

        try:
            await self._persist_mistake(request, response)
        except Exception as exc:
            raise DiagnosisError(
                "Failed to persist mistake record",
                details={"student_id": request.student_id, "error": str(exc)},
            ) from exc

        self._logger.info(
            "Diagnosis complete",
            extra={
                "student_id": request.student_id,
                "question_id": request.question_id,
                "error_category": response.error_category.value,
                "confidence": response.confidence,
            },
        )
        return response

    async def get_mistake_history(
        self,
        student_id: str,
        limit: int = 20,
    ) -> list[MistakeRecordResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(MistakeRecord)
                .where(MistakeRecord.student_id == student_id)
                .order_by(MistakeRecord.created_at.desc())
                .limit(limit)
            )
            records = result.scalars().all()
            return [MistakeRecordResponse.model_validate(r) for r in records]

    async def get_recurring_patterns(
        self,
        student_id: str,
    ) -> list[dict]:
        async with self._session_factory() as session:
            session: AsyncSession
            total_result = await session.execute(
                select(func.count(MistakeRecord.id)).where(
                    MistakeRecord.student_id == student_id,
                )
            )
            total = total_result.scalar() or 0
            if total == 0:
                return []

            group_result = await session.execute(
                select(
                    MistakeRecord.error_category,
                    func.count(MistakeRecord.id).label("cnt"),
                )
                .where(MistakeRecord.student_id == student_id)
                .group_by(MistakeRecord.error_category)
                .order_by(func.count(MistakeRecord.id).desc())
            )
            rows = group_result.all()
            patterns = []
            for row in rows:
                try:
                    cat = ErrorCategory(row.error_category)
                    description = self._registry.get_description(cat)
                except ValueError:
                    cat = None
                    description = ""
                patterns.append(
                    {
                        "error_category": row.error_category,
                        "count": row.cnt,
                        "percentage": round(row.cnt / total * 100, 1),
                        "description": description,
                    }
                )
            return patterns

    async def _load_student_context(
        self,
        request: MistakeDiagnosisRequest,
        context: dict,
    ) -> None:
        async with self._session_factory() as session:
            session: AsyncSession
            mastery_result = await session.execute(
                select(MasteryScore).where(
                    MasteryScore.student_id == request.student_id,
                )
            )
            context["mastery_scores"] = mastery_result.scalars().all()

            recent_result = await session.execute(
                select(MistakeRecord)
                .where(MistakeRecord.student_id == request.student_id)
                .order_by(MistakeRecord.created_at.desc())
                .limit(50)
            )
            recent = recent_result.scalars().all()
            context["recent_mistakes"] = [
                {
                    "id": r.id,
                    "error_category": r.error_category,
                    "concept_tag": r.concept_tag,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recent
            ]

        question_data = await self._fetch_question_data(request)
        context["question_data"] = question_data

    async def _fetch_question_data(
        self,
        request: MistakeDiagnosisRequest,
    ) -> dict:
        if request.question_type == "app" and self._app_q_service is not None:
            try:
                q = await self._app_q_service.get_question(str(request.question_id))
                return {
                    "subject": q.subject,
                    "topic": q.topic,
                    "subtopic": q.subtopic,
                    "difficulty": q.difficulty,
                    "question_type": q.question_type,
                    "question_text": q.question_text,
                    "correct_answer": q.correct_answer,
                    "options": q.options,
                }
            except Exception as exc:
                self._logger.warning(
                    "Failed to fetch app question",
                    extra={"question_id": request.question_id, "error": str(exc)},
                )

        if request.question_type == "test" and self._test_q_service is not None:
            try:
                q = await self._test_q_service.get_question(str(request.question_id))
                return {
                    "subject": q.subject,
                    "topic": q.topic,
                    "subtopic": q.subtopic,
                    "difficulty": q.difficulty,
                    "question_type": q.question_type,
                    "question_text": q.question_text,
                    "correct_answer": q.correct_answer,
                    "options": q.options,
                }
            except Exception as exc:
                self._logger.warning(
                    "Failed to fetch test question",
                    extra={"question_id": request.question_id, "error": str(exc)},
                )

        self._logger.warning("No question data available, using request defaults")
        return {
            "question_type": request.question_type,
            "question_text": request.response_text,
        }

    async def _compute_avg_response_time(
        self,
        student_id: str,
    ) -> float | None:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(func.avg(Attempt.response_time_seconds)).where(
                    Attempt.student_id == student_id
                )
            )
            avg = result.scalar()
            return float(avg) if avg is not None else None

    async def _persist_mistake(
        self,
        request: MistakeDiagnosisRequest,
        response: MistakeDiagnosisResponse,
    ) -> None:
        async with self._session_factory() as session:
            session: AsyncSession
            record = MistakeRecord(
                student_id=request.student_id,
                question_id=request.question_id,
                session_id=request.session_id,
                error_category=response.error_category.value,
                concept_tag=response.concept_tag,
                confidence=response.confidence,
                diagnosis_detail=response.diagnosis_detail,
                created_at=datetime.now(UTC),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            self._logger.debug(
                "Mistake record persisted",
                extra={
                    "record_id": record.id,
                    "student_id": request.student_id,
                    "error_category": response.error_category.value,
                },
            )
