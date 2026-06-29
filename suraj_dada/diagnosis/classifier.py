import re

from suraj_dada.config.loader import Settings
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.diagnosis import (
    ErrorCategory,
    MistakeDiagnosisRequest,
    MistakeDiagnosisResponse,
)

logger = get_logger("diagnosis.classifier")


class RootCauseClassifier:
    def __init__(self, config: Settings):
        self._config = config
        self._min_confidence = config.diagnosis.min_confidence

    async def classify(
        self,
        request: MistakeDiagnosisRequest,
        student_context: dict,
    ) -> MistakeDiagnosisResponse:
        mastery_scores: list = student_context.get("mastery_scores", [])
        recent_mistakes: list = student_context.get("recent_mistakes", [])
        question_data: dict = student_context.get("question_data", {})
        registry = student_context.get("_registry")

        response_time = request.response_time_seconds
        hints_used = request.hints_used
        question_type = question_data.get("question_type", request.question_type)
        question_text = question_data.get("question_text", "")
        correct_answer = question_data.get("correct_answer", "")
        topic = question_data.get("topic", "")
        subtopic = question_data.get("subtopic", "")
        difficulty = question_data.get("difficulty", 3)

        if not correct_answer:
            logger.warning("No correct_answer in question_data; using fallback defaults")

        expected_time = self._expected_time_for(question_type, difficulty)
        time_ratio = response_time / expected_time if expected_time > 0 else 1.0

        scores: dict[ErrorCategory, float] = {}

        is_wrong = bool(request.response_text and request.response_text != correct_answer)

        mastery_score = self._best_mastery(mastery_scores, topic, subtopic)

        if is_wrong and time_ratio < 0.3:
            scores[ErrorCategory.GUESSING] = 0.9

        if is_wrong and time_ratio > 1.5 and hints_used > 0:
            base = min(0.7 + hints_used * 0.05, 0.95)
            if mastery_score is not None and mastery_score < 50:
                base += 0.1
            if time_ratio > 2.5:
                base += 0.05
            scores[ErrorCategory.CONCEPT_MISUNDERSTOOD] = min(base, 0.95)

        if (
            is_wrong
            and question_type in ("numerical", "mcq")
            and self._sign_differs(request.response_text, correct_answer)
        ):
            scores[ErrorCategory.SIGN_UNIT_ERROR] = 0.85

        if (
            is_wrong
            and question_type == "numerical"
            and self._close_numeric(request.response_text, correct_answer)
        ):
            scores[ErrorCategory.CALCULATION_ERROR] = 0.75

        if is_wrong and topic and hints_used > 0 and time_ratio > 1.2:
            base = 0.7
            if mastery_score is not None and 50 <= mastery_score <= 75:
                base += 0.1
            scores[ErrorCategory.FORMULA_RECALL_FAILURE] = min(base, 0.9)

        if is_wrong and self._factor_mismatch(request.response_text, correct_answer, question_text):
            scores[ErrorCategory.MISREAD_QUESTION] = 0.8

        if not scores:
            scores[ErrorCategory.CARELESS_ARITHMETIC] = 0.5

        for cat in list(scores.keys()):
            recurrence = sum(1 for m in recent_mistakes if m.get("error_category") == cat.value)
            if recurrence > 0:
                scores[cat] = min(scores[cat] + recurrence * 0.05, 0.95)

        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]

        close_count = sum(1 for v in scores.values() if abs(v - confidence) < 0.15)
        if close_count > 1:
            confidence *= 0.85

        if (
            mastery_score is not None
            and mastery_score > 80
            and best_category
            in (
                ErrorCategory.CONCEPT_MISUNDERSTOOD,
                ErrorCategory.FORMULA_RECALL_FAILURE,
            )
        ):
            confidence *= 0.7

        confidence = max(self._min_confidence, min(confidence, 1.0))

        if registry:
            raw = registry.get_remediation_strategy(best_category)
            remediation = [s.strip().lstrip("- ") for s in raw.split("\n") if s.strip()]
        else:
            remediation = ["Review the topic and practice more problems."]

        return MistakeDiagnosisResponse(
            student_id=request.student_id,
            question_id=request.question_id,
            error_category=best_category,
            concept_tag=subtopic or topic or "general",
            confidence=round(confidence, 2),
            diagnosis_detail={
                "response_time_seconds": response_time,
                "expected_time_seconds": round(expected_time, 1),
                "time_ratio": round(time_ratio, 2),
                "hints_used": hints_used,
                "mastery_score": mastery_score,
                "question_type": question_type,
                "topic": topic,
                "subtopic": subtopic,
                "difficulty": difficulty,
                "category_scores": {k.value: round(v, 2) for k, v in scores.items()},
            },
            suggested_remediation=remediation,
        )

    def _expected_time_for(self, question_type: str, difficulty: int) -> float:
        base = {"mcq": 60.0, "numerical": 120.0, "assertion_reason": 45.0}.get(question_type, 90.0)
        return base * (0.8 + difficulty * 0.15)

    def _best_mastery(self, mastery_scores: list, topic: str, subtopic: str) -> float | None:
        candidates = []
        for m in mastery_scores:
            if isinstance(m, dict):
                if m.get("subtopic") == subtopic or m.get("topic") == topic:
                    candidates.append(m["score"])
            else:
                if (
                    hasattr(m, "subtopic")
                    and m.subtopic == subtopic
                    or hasattr(m, "topic")
                    and m.topic == topic
                ):
                    candidates.append(m.score)
        return max(candidates) if candidates else None

    def _sign_differs(self, response: str, correct: str) -> bool:
        try:
            r = (
                float(re.search(r"-?\d+\.?\d*", response).group())
                if re.search(r"-?\d+\.?\d*", response)
                else None
            )
            c = (
                float(re.search(r"-?\d+\.?\d*", correct).group())
                if re.search(r"-?\d+\.?\d*", correct)
                else None
            )
            if r is not None and c is not None:
                return abs(abs(r) - abs(c)) < 0.01 and r * c < 0
        except (ValueError, TypeError, AttributeError):
            pass
        return False

    def _close_numeric(self, response: str, correct: str) -> bool:
        try:
            r = (
                float(re.search(r"-?\d+\.?\d*", response).group())
                if re.search(r"-?\d+\.?\d*", response)
                else None
            )
            c = (
                float(re.search(r"-?\d+\.?\d*", correct).group())
                if re.search(r"-?\d+\.?\d*", correct)
                else None
            )
            if r is not None and c is not None:
                if abs(c) < 0.001:
                    return abs(r) < 0.01
                return abs(r - c) / max(abs(c), 0.01) < 0.15
        except (ValueError, TypeError, AttributeError):
            pass
        return False

    def _factor_mismatch(self, response: str, correct: str, question_text: str) -> bool:
        try:
            values = [float(v) for v in re.findall(r"\d+\.?\d*", question_text) if v]
            r = (
                float(re.search(r"-?\d+\.?\d*", response).group())
                if re.search(r"-?\d+\.?\d*", response)
                else None
            )
            c = (
                float(re.search(r"-?\d+\.?\d*", correct).group())
                if re.search(r"-?\d+\.?\d*", correct)
                else None
            )
            if r is not None and c is not None and abs(c) > 0.001:
                ratio = r / c
                for v in values:
                    if abs(abs(ratio) - v) < 0.05 or abs(abs(ratio) - 1.0 / v) < 0.05:
                        return True
        except (ValueError, TypeError, AttributeError, ZeroDivisionError):
            pass
        return False
