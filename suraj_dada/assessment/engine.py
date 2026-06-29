from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from suraj_dada.assessment.evaluator import AnswerEvaluator
from suraj_dada.assessment.tagger import AnswerTagger
from suraj_dada.config.loader import Settings, get_config
from suraj_dada.database.models import AppQuestion, TestQuestion
from suraj_dada.exceptions import AssessmentError, NotFoundError
from suraj_dada.logging_setup import get_logger
from suraj_dada.question_bank.test_questions import TestQuestionService
from suraj_dada.schemas.assessment import AssessmentCreate, AssessmentResponse, AssessmentResult
from suraj_dada.schemas.session import AttemptCreate
from suraj_dada.student.session_memory import SessionMemoryService

logger = get_logger("assessment.engine")


class AssessmentEngine:
    def __init__(
        self,
        session_factory,
        test_question_service: TestQuestionService,
        session_memory: SessionMemoryService,
        evaluator: AnswerEvaluator,
        tagger: AnswerTagger,
        config: Settings | None = None,
    ):
        self._session_factory = session_factory
        self._test_question_service = test_question_service
        self._session_memory = session_memory
        self._evaluator = evaluator
        self._tagger = tagger
        self._config = config or get_config()

    async def create_assessment(self, data: AssessmentCreate) -> AssessmentResponse:
        logger.info(
            "Creating assessment",
            extra={
                "student_id": data.student_id,
                "subject": data.subject,
                "question_count": len(data.question_ids),
            },
        )

        question_ids_str = [str(qid) for qid in data.question_ids]
        questions = await self._test_question_service.get_questions_by_ids(question_ids_str)

        if not questions:
            raise AssessmentError(
                "No valid questions found for assessment",
                details={"question_ids": data.question_ids},
            )

        session_resp = await self._session_memory.start_session(
            student_id=data.student_id,
            session_type="assessment",
        )

        question_dicts = []
        for q in questions:
            question_dicts.append(
                {
                    "id": q.id,
                    "subject": q.subject,
                    "topic": q.topic,
                    "subtopic": q.subtopic,
                    "difficulty": q.difficulty,
                    "question_type": q.question_type,
                    "question_text": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                }
            )

        response = AssessmentResponse(
            id=int(session_resp.id)
            if session_resp.id.isdigit()
            else hash(session_resp.id) % (10**8),
            student_id=data.student_id,
            subject=data.subject,
            status="in_progress",
            started_at=session_resp.started_at,
            ended_at=None,
            questions=question_dicts,
            score=0,
            results={},
        )

        logger.info(
            "Assessment created",
            extra={"session_id": session_resp.id, "question_count": len(question_dicts)},
        )
        return response

    async def submit_answer(
        self, assessment_id: str, question_id: str, student_answer: str
    ) -> dict[str, Any]:
        logger.info(
            "Submitting answer",
            extra={"assessment_id": assessment_id, "question_id": question_id},
        )

        session = await self._session_memory.get_session(assessment_id)
        if session.ended_at is not None:
            raise AssessmentError(
                "Assessment already completed", details={"assessment_id": assessment_id}
            )

        question = await self._find_question(question_id)
        if question is None:
            raise NotFoundError("Question", question_id)

        evaluation = await self._evaluator.evaluate(question, student_answer)
        tags = await self._tagger.tag(
            question,
            evaluation["is_correct"],
            response_time_seconds=0.0,
        )

        attempt_data = AttemptCreate(
            question_id=int(question_id),
            question_type=question.get("question_type", "test"),
            is_correct=evaluation["is_correct"],
            response_time_seconds=0.0,
            hints_used=0,
            retry_count=0,
            session_id=assessment_id,
        )
        await self._session_memory.record_attempt(assessment_id, attempt_data)

        result = {
            "question_id": question_id,
            "is_correct": evaluation["is_correct"],
            "expected_answer": evaluation["expected_answer"],
            "received_answer": evaluation["received_answer"],
            "evaluation_detail": evaluation["evaluation_detail"],
            "tags": tags,
        }

        logger.info(
            "Answer submitted",
            extra={
                "assessment_id": assessment_id,
                "question_id": question_id,
                "is_correct": evaluation["is_correct"],
            },
        )
        return result

    async def complete_assessment(self, assessment_id: str) -> AssessmentResult:
        logger.info("Completing assessment", extra={"assessment_id": assessment_id})

        session = await self._session_memory.get_session(assessment_id)
        await self._session_memory.end_session(assessment_id)

        attempts = await self._session_memory.get_session_attempts(assessment_id)

        total_questions = session.questions_count
        attempted = len(attempts)
        correct = sum(1 for a in attempts if a.is_correct)
        incorrect = attempted - correct
        score_percentage = round((correct / attempted * 100), 2) if attempted > 0 else 0.0

        topic_breakdown: dict[str, dict[str, Any]] = {}
        for a in attempts:
            key = f"{a.question_id}"
            if key not in topic_breakdown:
                topic_breakdown[key] = {"correct": 0, "incorrect": 0, "total": 0}
            topic_breakdown[key]["total"] += 1
            if a.is_correct:
                topic_breakdown[key]["correct"] += 1
            else:
                topic_breakdown[key]["incorrect"] += 1

        result = AssessmentResult(
            assessment_id=int(assessment_id)
            if assessment_id.isdigit()
            else hash(assessment_id) % (10**8),
            student_id=session.student_id,
            total_questions=total_questions,
            attempted=attempted,
            correct=correct,
            incorrect=incorrect,
            score_percentage=score_percentage,
            topic_breakdown=topic_breakdown,
            diagnosis_results=[],
        )

        logger.info(
            "Assessment completed",
            extra={"assessment_id": assessment_id, "score": score_percentage},
        )
        return result

    async def get_assessment(self, assessment_id: str) -> AssessmentResponse:
        session = await self._session_memory.get_session(assessment_id)

        return AssessmentResponse(
            id=int(assessment_id) if assessment_id.isdigit() else hash(assessment_id) % (10**8),
            student_id=session.student_id,
            subject="",
            status="completed" if session.ended_at else "in_progress",
            started_at=session.started_at,
            ended_at=session.ended_at,
            questions=[],
            score=session.correct_count,
            results={
                "questions_count": session.questions_count,
                "correct_count": session.correct_count,
            },
        )

    async def _find_question(self, question_id: str) -> dict[str, Any] | None:
        async with self._session_factory() as session:
            session: AsyncSession
            for model in (TestQuestion, AppQuestion):
                result = await session.execute(select(model).where(model.id == int(question_id)))
                record = result.scalar_one_or_none()
                if record is not None:
                    return {
                        "id": record.id,
                        "subject": record.subject,
                        "topic": record.topic,
                        "subtopic": record.subtopic,
                        "difficulty": record.difficulty,
                        "question_type": record.question_type,
                        "question_text": record.question_text,
                        "options": record.options,
                        "correct_answer": record.correct_answer,
                        "explanation": record.explanation,
                    }
            return None
