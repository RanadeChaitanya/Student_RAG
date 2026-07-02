from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from studob.config.loader import Settings
from studob.database.models import Attempt, MasteryScore, Student
from studob.exceptions import NotFoundError
from studob.logging_setup import get_logger
from studob.schemas.student import (
    MasteryScoreResponse,
    MasterySummaryResponse,
    MasteryUpdateSignals,
    WeakTopicInfo,
)

logger = get_logger("student.mastery")


class MasteryService:
    def __init__(self, session_factory, config: Settings):
        self._session_factory = session_factory
        self._config = config
        self._weakness_threshold = config.mastery.weakness_threshold
        self._prior_score = config.mastery.prior_score

    async def _ensure_student_exists(self, session: AsyncSession, student_id: str) -> None:
        result = await session.execute(select(Student).where(Student.id == student_id))
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Student", student_id)

    async def get_mastery(self, student_id: str, subtopic: str) -> MasteryScoreResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            await self._ensure_student_exists(session, student_id)
            result = await session.execute(
                select(MasteryScore).where(
                    and_(
                        MasteryScore.student_id == student_id,
                        MasteryScore.subtopic == subtopic,
                    )
                )
            )
            score = result.scalar_one_or_none()
            if score is None:
                raise NotFoundError("MasteryScore", f"{student_id}:{subtopic}")
            return MasteryScoreResponse.model_validate(score)

    async def get_all_mastery(self, student_id: str) -> list[MasteryScoreResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            await self._ensure_student_exists(session, student_id)
            result = await session.execute(
                select(MasteryScore).where(MasteryScore.student_id == student_id)
            )
            scores = result.scalars().all()
            return [MasteryScoreResponse.model_validate(s) for s in scores]

    async def update_mastery(
        self, student_id: str, subtopic: str, signals: dict | MasteryUpdateSignals
    ) -> MasteryScoreResponse:
        validated = MasteryUpdateSignals(**signals) if isinstance(signals, dict) else signals
        signals_dict = validated.model_dump()
        async with self._session_factory() as session:
            session: AsyncSession
            await self._ensure_student_exists(session, student_id)
            result = await session.execute(
                select(MasteryScore).where(
                    and_(
                        MasteryScore.student_id == student_id,
                        MasteryScore.subtopic == subtopic,
                    )
                )
            )
            mastery = result.scalar_one_or_none()
            if mastery is None:
                mastery = MasteryScore(
                    student_id=student_id,
                    subject=validated.subject,
                    topic=validated.topic,
                    subtopic=subtopic,
                    score=self._prior_score,
                    confidence=0.5,
                    attempts=0,
                    last_updated=datetime.now(UTC),
                )
                session.add(mastery)
                await session.flush()

            current_score = mastery.score
            new_score = await self.compute_mastery_update(current_score, signals_dict)
            mastery.score = round(new_score, 2)
            mastery.attempts += 1
            confidence_delta = 0.05 if validated.correctness > 0.5 else -0.02
            mastery.confidence = max(0.0, min(1.0, mastery.confidence + confidence_delta))
            mastery.last_updated = datetime.now(UTC)
            await session.commit()
            await session.refresh(mastery)
            logger.info(
                "Mastery updated",
                extra={
                    "student_id": student_id,
                    "subtopic": subtopic,
                    "previous_score": current_score,
                    "new_score": new_score,
                },
            )
            return MasteryScoreResponse.model_validate(mastery)

    async def compute_mastery_update(self, current_score: float, signals: dict) -> float:
        config = self._config.mastery
        correctness = signals.get("correctness", 0)
        response_time_ratio = signals.get("response_time_ratio", 1.0)
        hints_used = signals.get("hints_used_count", 0)
        retries = signals.get("retry_count", 0)
        recurrence_flag = signals.get("recurrence_flag", 0)
        qconf_score = signals.get("qconf_score", None)

        time_signal = 1.0 - min(response_time_ratio, 2.0) / 2.0

        qconf_boost = 0.0
        if qconf_score is not None:
            if qconf_score >= 0.75:
                qconf_boost = 0.05
            elif qconf_score < 0.45:
                qconf_boost = -0.05

        signal_strength = (
            (correctness * config.correct_weight)
            + (time_signal * config.time_weight)
            - (hints_used * config.hint_penalty)
            - (retries * 0.1)
            - (recurrence_flag * config.recurrence_penalty)
            + qconf_boost
        )
        signal_strength = max(-1.0, min(1.0, signal_strength))

        if signal_strength > 0:
            new_score = current_score + (
                signal_strength * (100.0 - current_score) * config.bayesian_k / 100.0
            )
        else:
            new_score = current_score + (
                signal_strength * current_score * config.bayesian_k / 100.0
            )

        new_score = max(0.0, min(100.0, new_score))
        logger.debug(
            "compute_mastery_update",
            extra={
                "current_score": current_score,
                "new_score": new_score,
                "signal_strength": signal_strength,
                "correctness": correctness,
                "response_time_ratio": response_time_ratio,
                "hints_used": hints_used,
                "retries": retries,
                "recurrence_flag": recurrence_flag,
            },
        )
        return new_score

    async def get_mastery_summary(self, student_id: str) -> MasterySummaryResponse:
        scores = await self.get_all_mastery(student_id)
        if not scores:
            return MasterySummaryResponse(
                student_id=student_id,
                overall_score=0.0,
                subject_breakdown={},
                weak_topics=[],
                strengths=[],
            )

        subject_groups: dict[str, list[MasteryScoreResponse]] = {}
        for s in scores:
            subject_groups.setdefault(s.subject, []).append(s)

        subject_breakdown = {}
        overall_total = 0.0
        overall_count = 0
        for subject, subs in subject_groups.items():
            avg = sum(s.score for s in subs) / len(subs)
            subject_breakdown[subject] = round(avg, 2)
            overall_total += sum(s.score for s in subs)
            overall_count += len(subs)

        overall_score = round(overall_total / overall_count, 2) if overall_count > 0 else 0.0

        weak_topics = []
        strengths = []
        for s in scores:
            gap = max(0.0, self._weakness_threshold - s.score)
            info = WeakTopicInfo(
                subject=s.subject,
                topic=s.topic,
                subtopic=s.subtopic,
                score=s.score,
                gap=gap,
            )
            if s.score < self._weakness_threshold:
                weak_topics.append(info)
            else:
                strengths.append(info)

        weak_topics.sort(key=lambda x: x.gap, reverse=True)
        strengths.sort(key=lambda x: x.score, reverse=True)

        return MasterySummaryResponse(
            student_id=student_id,
            overall_score=overall_score,
            subject_breakdown=subject_breakdown,
            weak_topics=weak_topics,
            strengths=strengths,
        )

    async def identify_weak_topics(self, student_id: str) -> list[WeakTopicInfo]:
        summary = await self.get_mastery_summary(student_id)
        return summary.weak_topics

    async def get_qconf_stats(self, student_id: str) -> dict:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(Attempt.question_confidence_score)
                .where(
                    and_(
                        Attempt.student_id == student_id,
                        Attempt.question_confidence_score.isnot(None),
                    )
                )
                .order_by(Attempt.answered_at.desc())
                .limit(100)
            )
            scores = [row[0] for row in result.all() if row[0] is not None]

        if not scores:
            return {
                "average_qconf": 0.0,
                "qconf_distribution": {"high": 0, "medium": 0, "low": 0},
            }

        avg = sum(scores) / len(scores)
        high = sum(1 for s in scores if s >= 0.75)
        medium = sum(1 for s in scores if 0.45 <= s < 0.75)
        low = sum(1 for s in scores if s < 0.45)

        return {
            "average_qconf": round(avg, 4),
            "qconf_distribution": {"high": high, "medium": medium, "low": low},
        }
