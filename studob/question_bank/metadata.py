from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from studob.database.models import AppQuestion
from studob.logging_setup import get_logger
from studob.schemas.question import MetadataFilterResult, QuestionFilter

logger = get_logger("question_bank.metadata")


class MetadataFilterService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def filter_by_criteria(
        self,
        filters: QuestionFilter,
        exclude_ids: list[str] | None = None,
    ) -> MetadataFilterResult:
        async with self._session_factory() as session:
            session: AsyncSession
            query = select(AppQuestion.id)
            conditions = []
            if filters.subject is not None:
                conditions.append(AppQuestion.subject == filters.subject)
            if filters.topic is not None:
                conditions.append(AppQuestion.topic == filters.topic)
            if filters.subtopic is not None:
                conditions.append(AppQuestion.subtopic == filters.subtopic)
            if filters.difficulty_min is not None:
                conditions.append(AppQuestion.difficulty >= filters.difficulty_min)
            if filters.difficulty_max is not None:
                conditions.append(AppQuestion.difficulty <= filters.difficulty_max)
            if filters.question_type is not None:
                conditions.append(AppQuestion.question_type == filters.question_type)
            if filters.tags is not None:
                for tag in filters.tags:
                    conditions.append(AppQuestion.tags.any(tag))
            if exclude_ids:
                int_exclude = [int(i) for i in exclude_ids]
                conditions.append(AppQuestion.id.notin_(int_exclude))
            if conditions:
                query = query.where(and_(*conditions))
            result = await session.execute(query)
            ids = [row[0] for row in result.all()]
            logger.info(
                "Metadata filter applied",
                extra={
                    "filter_count": len(ids),
                    "exclude_count": len(exclude_ids) if exclude_ids else 0,
                },
            )
            return MetadataFilterResult(
                question_ids=ids,
                total_count=len(ids),
                filter_criteria=filters,
            )
