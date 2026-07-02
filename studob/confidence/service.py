from studob.confidence.calculator import ConfidenceCalculator
from studob.confidence.models import QConfResult
from studob.logging_setup import get_logger

logger = get_logger("confidence.service")


class ConfidenceService:
    def __init__(self, calculator: ConfidenceCalculator | None = None):
        self._calculator = calculator or ConfidenceCalculator()

    def compute_confidence(
        self,
        is_correct: bool,
        response_time_seconds: float,
        hints_used: int = 0,
        retry_count: int = 0,
        difficulty: int = 1,
        is_recurrence: bool = False,
    ) -> QConfResult:
        return self._calculator.compute(
            is_correct=is_correct,
            response_time_seconds=response_time_seconds,
            hints_used=hints_used,
            retry_count=retry_count,
            difficulty=difficulty,
            is_recurrence=is_recurrence,
        )
