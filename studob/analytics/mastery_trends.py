from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from studob.database.models import MasteryScore
from studob.logging_setup import get_logger
from studob.schemas.analytics import MasteryTrendPoint

logger = get_logger("analytics.mastery_trends")


class MasteryTrendService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_mastery_trend(self, student_id: str, days: int = 30) -> list[MasteryTrendPoint]:
        logger.info("Fetching mastery trend", extra={"student_id": student_id, "days": days})
        cutoff = datetime.now(UTC) - timedelta(days=days)

        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(MasteryScore)
                .where(
                    MasteryScore.student_id == student_id,
                    MasteryScore.last_updated >= cutoff,
                )
                .order_by(MasteryScore.last_updated.asc())
            )
            scores = result.scalars().all()

        grouped: dict[str, list[MasteryScore]] = defaultdict(list)
        for s in scores:
            date_key = s.last_updated.strftime("%Y-%m-%d")
            grouped[date_key].append(s)

        trend_points: list[MasteryTrendPoint] = []
        for date_key in sorted(grouped.keys()):
            day_scores = grouped[date_key]
            for s in day_scores:
                trend_points.append(
                    MasteryTrendPoint(
                        date=s.last_updated,
                        subject=s.subject,
                        topic=s.topic,
                        subtopic=s.subtopic,
                        score=s.score,
                    )
                )

        logger.info(
            "Mastery trend retrieved", extra={"student_id": student_id, "points": len(trend_points)}
        )
        return trend_points
