from typing import Any

from studob.exceptions import AssessmentError
from studob.logging_setup import get_logger

logger = get_logger("assessment.evaluator")


class AnswerEvaluator:
    async def evaluate(self, question: dict, student_answer: str) -> dict[str, Any]:
        qtype = question.get("question_type", "mcq")
        correct_answer = str(question.get("correct_answer", "")).strip()
        student_answer = student_answer.strip()
        expected_answer = correct_answer
        is_correct = False
        evaluation_detail = ""

        try:
            if qtype in ("mcq", "assertion_reason", "multiple_choice"):
                is_correct = student_answer.upper() == correct_answer.upper()
                evaluation_detail = (
                    "Correct match."
                    if is_correct
                    else f"Expected '{correct_answer}', got '{student_answer}'."
                )

            elif qtype == "numerical":
                tolerance = float(question.get("tolerance", 0.01))
                try:
                    student_val = float(student_answer)
                    correct_val = float(correct_answer)
                    is_correct = abs(student_val - correct_val) <= tolerance
                    evaluation_detail = (
                        f"Within tolerance (difference={abs(student_val - correct_val):.4f})."
                        if is_correct
                        else f"Expected ~{correct_val}, got {student_val} (difference={abs(student_val - correct_val):.4f})."  # noqa: E501
                    )
                except ValueError:
                    is_correct = False
                    evaluation_detail = f"Could not parse numerical answer '{student_answer}'."

            else:
                is_correct = student_answer.upper() == correct_answer.upper()
                evaluation_detail = (
                    "Correct match."
                    if is_correct
                    else f"Expected '{correct_answer}', got '{student_answer}'."
                )

        except Exception as exc:
            raise AssessmentError(
                "Evaluation failed",
                details={"question_id": question.get("id"), "error": str(exc)},
            ) from exc

        result = {
            "is_correct": is_correct,
            "expected_answer": expected_answer,
            "received_answer": student_answer,
            "evaluation_detail": evaluation_detail,
        }

        logger.info(
            "Answer evaluated",
            extra={
                "question_id": question.get("id"),
                "is_correct": is_correct,
                "question_type": qtype,
            },
        )
        return result
