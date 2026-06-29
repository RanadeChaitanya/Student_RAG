from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from suraj_dada.database.models import TestQuestion
from suraj_dada.exceptions import NotFoundError
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.question import QuestionFilter, TestQuestionCreate, TestQuestionResponse

logger = get_logger("question_bank.test_questions")


class TestQuestionService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def create_question(self, data: TestQuestionCreate) -> TestQuestionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            question = TestQuestion(
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
                year=data.year,
                exam_type=data.exam_type,
                is_active=data.is_active,
            )
            session.add(question)
            await session.commit()
            await session.refresh(question)
            logger.info("Created test question", extra={"question_id": question.id})
            return TestQuestionResponse.model_validate(question)

    async def get_question(self, question_id: str) -> TestQuestionResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(
                select(TestQuestion).where(TestQuestion.id == int(question_id))
            )
            question = result.scalar_one_or_none()
            if question is None:
                raise NotFoundError("TestQuestion", question_id)
            return TestQuestionResponse.model_validate(question)

    async def bulk_create(self, questions: list[TestQuestionCreate]) -> list[TestQuestionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            models = []
            for data in questions:
                q = TestQuestion(
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
                    year=data.year,
                    exam_type=data.exam_type,
                    is_active=data.is_active,
                )
                session.add(q)
                models.append(q)
            await session.commit()
            for q in models:
                await session.refresh(q)
            logger.info("Bulk created test questions", extra={"count": len(models)})
            return [TestQuestionResponse.model_validate(q) for q in models]

    async def search_by_metadata(self, filters: QuestionFilter) -> list[TestQuestionResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            query = select(TestQuestion)
            conditions = []
            if filters.subject is not None:
                conditions.append(TestQuestion.subject == filters.subject)
            if filters.topic is not None:
                conditions.append(TestQuestion.topic == filters.topic)
            if filters.subtopic is not None:
                conditions.append(TestQuestion.subtopic == filters.subtopic)
            if filters.difficulty_min is not None:
                conditions.append(TestQuestion.difficulty >= filters.difficulty_min)
            if filters.difficulty_max is not None:
                conditions.append(TestQuestion.difficulty <= filters.difficulty_max)
            if filters.question_type is not None:
                conditions.append(TestQuestion.question_type == filters.question_type)
            if filters.tags is not None:
                for tag in filters.tags:
                    conditions.append(TestQuestion.tags.any(tag))
            if conditions:
                query = query.where(and_(*conditions))
            result = await session.execute(query)
            questions = result.scalars().all()
            return [TestQuestionResponse.model_validate(q) for q in questions]

    async def get_questions_by_ids(self, ids: list[str]) -> list[TestQuestionResponse]:
        int_ids = [int(i) for i in ids]
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(TestQuestion).where(TestQuestion.id.in_(int_ids)))
            questions = result.scalars().all()
            return [TestQuestionResponse.model_validate(q) for q in questions]
