from typing import Any

from studob.exceptions import NotFoundError
from studob.logging_setup import get_logger
from studob.student.session_memory import SessionMemoryService

logger = get_logger("analytics.session_reports")


class SessionReportService:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._session_memory = SessionMemoryService(session_factory)

    async def generate_report(self, session_id: str) -> dict[str, Any]:
        logger.info("Generating session report", extra={"session_id": session_id})

        try:
            session = await self._session_memory.get_session(session_id)
            attempts = await self._session_memory.get_session_attempts(session_id)
        except NotFoundError as e:
            raise NotFoundError("Session", session_id) from e

        total_questions = session.questions_count
        correct = sum(1 for a in attempts if a.is_correct)
        incorrect = total_questions - correct
        total_time = sum(a.response_time_seconds for a in attempts)

        report = {
            "session_id": session_id,
            "student_id": session.student_id,
            "session_type": session.session_type,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_minutes": round(
                (session.ended_at - session.started_at).total_seconds() / 60, 2
            )
            if session.ended_at and session.started_at
            else None,
            "questions_attempted": total_questions,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "accuracy_percent": round((correct / total_questions * 100), 2)
            if total_questions > 0
            else 0.0,
            "total_time_spent_seconds": round(total_time, 2),
            "mastery_delta": session.mastery_delta,
            "attempts": [
                {
                    "question_id": a.question_id,
                    "is_correct": a.is_correct,
                    "response_time_seconds": a.response_time_seconds,
                    "hints_used": a.hints_used,
                    "retry_count": a.retry_count,
                    "answered_at": a.answered_at.isoformat() if a.answered_at else None,
                }
                for a in attempts
            ],
        }

        logger.info("Session report generated", extra={"session_id": session_id})
        return report
