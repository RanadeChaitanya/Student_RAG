from typing import Any

from suraj_dada.logging_setup import get_logger

logger = get_logger("assessment.tagger")


class AnswerTagger:
    async def tag(
        self, question: dict, is_correct: bool, response_time_seconds: float
    ) -> dict[str, Any]:
        subject = question.get("subject", "unknown")
        topic = question.get("topic", "unknown")
        subtopic = question.get("subtopic", "unknown")
        difficulty = question.get("difficulty", 3)
        question_type = question.get("question_type", "unknown")

        if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
            difficulty = 3

        result = {
            "subject": subject,
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "question_type": question_type,
        }

        logger.info(
            "Answer tagged",
            extra={
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "difficulty": difficulty,
                "question_type": question_type,
                "is_correct": is_correct,
                "response_time_seconds": response_time_seconds,
            },
        )
        return result
