from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from studob.database.models import AppQuestion
from studob.exceptions import NotFoundError
from studob.logging_setup import get_logger
from studob.schemas.question import AppQuestionCreate, AppQuestionResponse, QuestionFilter

logger = get_logger("question_bank.app_questions")


class AppQuestionService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def create_question(self, data: AppQuestionCreate) -> AppQuestionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            question = AppQuestion(
                subject=data.subject,
                topic=data.topic,
                subtopic=data.subtopic,
                difficulty=data.difficulty,
                question_type=data.question_type,
                question_text=data.question_text,
                options=data.options,
                correct_answer=data.correct_answer,
                explanation=data.explanation,
                tags=data.tags,
                source=data.source,
                is_active=data.is_active,
            )
            session.add(question)
            await session.commit()
            await session.refresh(question)
            logger.info("Created app question", extra={"question_id": question.id})
            return AppQuestionResponse.model_validate(question)

    async def get_question(self, question_id: str) -> AppQuestionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(AppQuestion).where(AppQuestion.id == int(question_id))
            )
            question = result.scalar_one_or_none()
            if question is None:
                raise NotFoundError("AppQuestion", question_id)
            return AppQuestionResponse.model_validate(question)

    async def bulk_create(self, questions: list[AppQuestionCreate]) -> list[AppQuestionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            models = []
            for data in questions:
                q = AppQuestion(
                    subject=data.subject,
                    topic=data.topic,
                    subtopic=data.subtopic,
                    difficulty=data.difficulty,
                    question_type=data.question_type,
                    question_text=data.question_text,
                    options=data.options,
                    correct_answer=data.correct_answer,
                    explanation=data.explanation,
                    tags=data.tags,
                    source=data.source,
                    is_active=data.is_active,
                )
                session.add(q)
                models.append(q)
            await session.commit()
            for q in models:
                await session.refresh(q)
            logger.info("Bulk created app questions", extra={"count": len(models)})
            return [AppQuestionResponse.model_validate(q) for q in models]

    async def search_by_metadata(self, filters: QuestionFilter) -> list[AppQuestionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            query = select(AppQuestion)
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
            if conditions:
                query = query.where(and_(*conditions))
            result = await session.execute(query)
            questions = result.scalars().all()
            return [AppQuestionResponse.model_validate(q) for q in questions]

    async def get_all_questions(self) -> list[AppQuestionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(AppQuestion))
            questions = result.scalars().all()
            return [AppQuestionResponse.model_validate(q) for q in questions]

    async def get_questions_by_concept(self, concept_tag: str, difficulty_min: int = 1, difficulty_max: int = 5) -> list[AppQuestionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            query = select(AppQuestion).where(
                and_(
                    AppQuestion.difficulty >= difficulty_min,
                    AppQuestion.difficulty <= difficulty_max,
                )
            )
            result = await session.execute(query)
            questions = result.scalars().all()
            tag_lower = concept_tag.lower()
            matched = [
                q for q in questions
                if tag_lower in q.subtopic.lower()
                or tag_lower in q.topic.lower()
                or tag_lower in q.subject.lower()
            ]
            return [AppQuestionResponse.model_validate(q) for q in matched]

    async def get_questions_by_ids(self, ids: list[str]) -> list[AppQuestionResponse]:
        int_ids = [int(i) for i in ids]
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(AppQuestion).where(AppQuestion.id.in_(int_ids)))
            questions = result.scalars().all()
            return [AppQuestionResponse.model_validate(q) for q in questions]

    async def get_questions_by_concepts_batch(self, concept_tags: list[str], difficulty_min: int = 1, difficulty_max: int = 5) -> dict[str, list[AppQuestionResponse]]:
        async with self._session_factory() as session:
            session: AsyncSession
            query = select(AppQuestion).where(
                and_(
                    AppQuestion.difficulty >= difficulty_min,
                    AppQuestion.difficulty <= difficulty_max,
                )
            )
            result = await session.execute(query)
            all_questions = result.scalars().all()
            result_map: dict[str, list[AppQuestionResponse]] = {}
            for tag in concept_tags:
                tag_lower = tag.lower()
                tag_parts = set()
                tag_parts.add(tag_lower)
                tag_parts.add(tag_lower.replace("-", " "))
                for part in tag_lower.replace("-", " ").split():
                    if len(part) > 1:
                        tag_parts.add(part)
                matched = [
                    AppQuestionResponse.model_validate(q) for q in all_questions
                    if any(
                        p in q.subtopic.lower()
                        or p in q.topic.lower()
                        or p in q.subject.lower()
                        for p in tag_parts
                    )
                ]
                result_map[tag] = matched
            return result_map
