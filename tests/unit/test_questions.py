import pytest

from studob.schemas.question import AppQuestionCreate, TestQuestionCreate


class TestAppQuestions:
    @pytest.mark.asyncio
    async def test_create_and_get(self, app_questions):
        data = AppQuestionCreate(
            subject="physics",
            topic="kinematics",
            subtopic="motion in 1d",
            difficulty=2,
            question_type="mcq",
            question_text="Test Q?",
            correct_answer="A",
            explanation="e",
            tags=["test"],
        )
        created = await app_questions.create_question(data)
        assert created.id is not None

        fetched = await app_questions.get_question(str(created.id))
        assert fetched.question_text == "Test Q?"

    @pytest.mark.asyncio
    async def test_bulk_create(self, app_questions):
        data = [
            AppQuestionCreate(
                subject="physics",
                topic="kinematics",
                subtopic="motion in 1d",
                difficulty=2,
                question_type="mcq",
                question_text=f"Q{i}?",
                correct_answer="A",
                explanation="e",
                tags=["test"],
            )
            for i in range(3)
        ]
        created = await app_questions.bulk_create(data)
        assert len(created) == 3

    @pytest.mark.asyncio
    async def test_search_by_metadata(self, app_questions):
        from studob.schemas.question import QuestionFilter

        data = AppQuestionCreate(
            subject="physics",
            topic="kinematics",
            subtopic="motion in 1d",
            difficulty=2,
            question_type="mcq",
            question_text="Search test?",
            correct_answer="A",
            explanation="e",
            tags=["test"],
        )
        await app_questions.create_question(data)

        results = await app_questions.search_by_metadata(QuestionFilter(subject="physics"))
        assert len(results) > 0


class TestTestQuestions:
    @pytest.mark.asyncio
    async def test_create_and_get(self, session_factory):
        from studob.question_bank.test_questions import TestQuestionService

        svc = TestQuestionService(session_factory)
        data = TestQuestionCreate(
            subject="physics",
            topic="kinematics",
            subtopic="motion in 1d",
            difficulty=2,
            question_type="numerical",
            question_text="Num test?",
            correct_answer="42",
            explanation="e",
            tags=["test"],
            year=2023,
            exam_type="JEE Main",
        )
        created = await svc.create_question(data)
        assert created.id is not None

        fetched = await svc.get_question(str(created.id))
        assert fetched.question_text == "Num test?"
