import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from studob.confidence import ConfidenceCalculator
from studob.database.models import Attempt, Session, Student
from studob.exceptions import NotFoundError
from studob.logging_setup import get_logger
from studob.schemas.session import AttemptCreate, AttemptResponse, SessionResponse

logger = get_logger("student.session_memory")


class SessionMemoryService:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._confidence_calculator = ConfidenceCalculator()

    async def start_session(self, student_id: str, session_type: str) -> SessionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Student).where(Student.id == student_id))
            if result.scalar_one_or_none() is None:
                raise NotFoundError("Student", student_id)
            record = Session(
                id=str(uuid.uuid4()),
                student_id=student_id,
                session_type=session_type,
                started_at=datetime.now(UTC),
                questions_count=0,
                correct_count=0,
                mastery_delta=0.0,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info(
                "Session started",
                extra={
                    "session_id": record.id,
                    "student_id": student_id,
                    "session_type": session_type,
                },
            )
            return SessionResponse.model_validate(record)

    async def end_session(self, session_id: str, mastery_delta: float | None = None) -> SessionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Session).where(Session.id == session_id))
            record = result.scalar_one_or_none()
            if record is None:
                raise NotFoundError("Session", session_id)
            record.ended_at = datetime.now(UTC)
            if mastery_delta is not None:
                record.mastery_delta = mastery_delta
            await session.commit()
            await session.refresh(record)
            logger.info("Session ended", extra={"session_id": session_id})
            return SessionResponse.model_validate(record)

    async def record_attempt(self, session_id: str, data: AttemptCreate) -> AttemptResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Session).where(Session.id == session_id))
            sess_record = result.scalar_one_or_none()
            if sess_record is None:
                raise NotFoundError("Session", session_id)
            result = await session.execute(
                select(Student).where(Student.id == sess_record.student_id)
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError("Student", sess_record.student_id)

            qconf_result = self._confidence_calculator.compute(
                is_correct=data.is_correct,
                response_time_seconds=data.response_time_seconds,
                hints_used=data.hints_used,
                retry_count=data.retry_count,
                difficulty=data.difficulty,
                is_recurrence=data.is_recurrence,
            )

            attempt = Attempt(
                student_id=sess_record.student_id,
                question_id=data.question_id,
                question_type=data.question_type,
                is_correct=data.is_correct,
                response_time_seconds=data.response_time_seconds,
                hints_used=data.hints_used,
                retry_count=data.retry_count,
                answered_at=datetime.now(UTC),
                session_id=session_id,
                question_confidence_score=qconf_result.score,
            )
            session.add(attempt)
            sess_record.questions_count += 1
            if data.is_correct:
                sess_record.correct_count += 1
            await session.commit()
            await session.refresh(attempt)
            logger.info(
                "Attempt recorded",
                extra={
                    "session_id": session_id,
                    "question_id": data.question_id,
                    "is_correct": data.is_correct,
                    "qconf_score": qconf_result.score,
                    "qconf_classification": qconf_result.classification,
                },
            )
            return AttemptResponse.model_validate(attempt)

    async def get_session(self, session_id: str) -> SessionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Session).where(Session.id == session_id))
            record = result.scalar_one_or_none()
            if record is None:
                raise NotFoundError("Session", session_id)
            return SessionResponse.model_validate(record)

    async def get_session_attempts(self, session_id: str) -> list[AttemptResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(Attempt)
                .where(Attempt.session_id == session_id)
                .order_by(Attempt.answered_at)
            )
            attempts = result.scalars().all()
            return [AttemptResponse.model_validate(a) for a in attempts]

    async def get_sessions_by_student(self, student_id: str) -> list[SessionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(Session)
                .where(Session.student_id == student_id)
                .order_by(desc(Session.started_at))
            )
            records = result.scalars().all()
            return [SessionResponse.model_validate(r) for r in records]

    async def get_active_sessions(self, student_id: str) -> list[SessionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(Session).where(
                    and_(
                        Session.student_id == student_id,
                        Session.ended_at.is_(None),
                    )
                )
            )
            records = result.scalars().all()
            return [SessionResponse.model_validate(r) for r in records]

    async def get_recent_concepts(self, student_id: str, limit: int = 5) -> list[str]:
        async with self._session_factory() as session:
            session: AsyncSession
            from studob.database.models import AppQuestion

            result = await session.execute(
                select(Attempt)
                .where(Attempt.student_id == student_id)
                .order_by(desc(Attempt.answered_at))
                .limit(limit * 3)
            )
            attempts = result.scalars().all()
            seen = []
            for a in attempts:
                q_result = await session.execute(
                    select(AppQuestion.subtopic).where(AppQuestion.id == a.question_id)
                )
                subtopic = q_result.scalar_one_or_none()
                if subtopic is not None and subtopic not in seen:
                    seen.append(subtopic)
                if len(seen) >= limit:
                    break
            return seen

    async def get_seen_question_ids(self, student_id: str, session_id: str) -> list[str]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(Attempt.question_id).where(
                    and_(
                        Attempt.student_id == student_id,
                        Attempt.session_id == session_id,
                    )
                )
            )
            return [str(row[0]) for row in result.all()]
