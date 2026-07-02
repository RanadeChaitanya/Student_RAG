
from studob.confidence.constants import (
    DEFAULT_PENALTIES,
    DEFAULT_THRESHOLDS,
    DEFAULT_TIME_PARAMS,
    DEFAULT_WEIGHTS,
    ConfidenceThresholds,
    ConfidenceWeights,
    ExpectedTimeParams,
    PenaltyParams,
)
from studob.confidence.models import ConfidenceFactors, QConfResult
from studob.logging_setup import get_logger

logger = get_logger("confidence.calculator")


class ConfidenceCalculator:
    def __init__(
        self,
        weights: ConfidenceWeights | None = None,
        thresholds: ConfidenceThresholds | None = None,
        time_params: ExpectedTimeParams | None = None,
        penalties: PenaltyParams | None = None,
    ):
        self._weights = weights or DEFAULT_WEIGHTS
        self._thresholds = thresholds or DEFAULT_THRESHOLDS
        self._time_params = time_params or DEFAULT_TIME_PARAMS
        self._penalties = penalties or DEFAULT_PENALTIES

    def compute(
        self,
        is_correct: bool,
        response_time_seconds: float,
        hints_used: int = 0,
        retry_count: int = 0,
        difficulty: int = 1,
        is_recurrence: bool = False,
    ) -> QConfResult:
        correctness_signal = 1.0 if is_correct else 0.0

        expected_time = self._time_params.base_seconds + (
            difficulty * self._time_params.per_difficulty
        )
        time_ratio = response_time_seconds / expected_time if expected_time > 0 else 1.0

        if is_correct:
            time_factor = max(0.0, min(1.0, 1.0 - (time_ratio - 0.3) / 2.0))
        else:
            time_factor = max(0.0, min(1.0, 0.5 - time_ratio * 0.25))

        max_h = self._penalties.max_hints
        hint_penalty = min(hints_used, max_h) * self._penalties.hint_penalty_per_unit
        max_r = self._penalties.max_retries
        retry_penalty = min(retry_count, max_r) * self._penalties.retry_penalty_per_unit

        difficulty_boost = 0.0
        if is_correct:
            diff_factor = max(0, difficulty - 1) / 4.0
            difficulty_boost = diff_factor * self._weights.difficulty

        recurrence_penalty = self._penalties.recurrence_penalty if is_recurrence else 0.0

        score = (
            self._weights.correctness * correctness_signal
            + self._weights.response_time * time_factor
            - hint_penalty
            - retry_penalty
            + difficulty_boost
            - recurrence_penalty
        )

        score = max(0.0, min(1.0, score))

        if score >= self._thresholds.high_confidence:
            classification = "high"
        elif score >= self._thresholds.medium_confidence:
            classification = "medium"
        else:
            classification = "low"

        factors = ConfidenceFactors(
            correctness_signal=round(correctness_signal, 4),
            time_factor=round(time_factor, 4),
            hint_penalty=round(hint_penalty, 4),
            retry_penalty=round(retry_penalty, 4),
            difficulty_boost=round(difficulty_boost, 4),
            recurrence_penalty=round(recurrence_penalty, 4),
        )

        result = QConfResult(
            score=round(score, 4),
            factors=factors,
            classification=classification,
        )

        logger.debug(
            "Confidence computed",
            extra={
                "is_correct": is_correct,
                "response_time": response_time_seconds,
                "difficulty": difficulty,
                "score": result.score,
                "classification": classification,
            },
        )

        return result
