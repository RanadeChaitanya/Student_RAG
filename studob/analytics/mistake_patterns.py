from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from studob.database.models import MistakeRecord
from studob.logging_setup import get_logger
from studob.schemas.analytics import MistakePatternSummary

logger = get_logger("analytics.mistake_patterns")


class MistakePatternService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_patterns(self, student_id: str) -> list[MistakePatternSummary]:
        logger.info("Fetching mistake patterns", extra={"student_id": student_id})

        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(MistakeRecord)
                .where(MistakeRecord.student_id == student_id)
                .order_by(MistakeRecord.created_at.desc())
            )
            records = result.scalars().all()

        total = len(records)
        if total == 0:
            logger.info("No mistake records found", extra={"student_id": student_id})
            return []

        category_counts: Counter = Counter()
        category_concepts: dict[str, list[str]] = defaultdict(list)

        for record in records:
            category_counts[record.error_category] += 1
            category_concepts[record.error_category].append(record.concept_tag)

        patterns: list[MistakePatternSummary] = []
        for error_category, count in category_counts.most_common():
            concept_counter = Counter(category_concepts[error_category])
            top_concepts = [concept for concept, _ in concept_counter.most_common(5)]
            frequency_percent = round((count / total) * 100, 2)

            patterns.append(
                MistakePatternSummary(
                    error_category=error_category,
                    count=count,
                    frequency_percent=frequency_percent,
                    common_concepts=top_concepts,
                )
            )

        logger.info(
            "Mistake patterns computed",
            extra={"student_id": student_id, "pattern_count": len(patterns)},
        )
        return patterns
