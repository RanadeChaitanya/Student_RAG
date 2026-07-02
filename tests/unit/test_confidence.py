import pytest

from studob.confidence import (
    ConfidenceAnalytics,
    ConfidenceCalculator,
    ConfidenceService,
    QConfResult,
)
from studob.confidence.constants import (
    DEFAULT_THRESHOLDS,
    ConfidenceThresholds,
    ConfidenceWeights,
    ExpectedTimeParams,
    PenaltyParams,
)
from studob.confidence.models import ConfidenceFactors


class TestConfidenceCalculator:
    def setup_method(self):
        self.calc = ConfidenceCalculator()

    def test_correct_fast_answer_high_confidence(self):
        result = self.calc.compute(
            is_correct=True,
            response_time_seconds=10.0,
            hints_used=0,
            retry_count=0,
            difficulty=3,
        )
        assert result.score >= 0.75
        assert result.classification == "high"
        assert result.factors.correctness_signal == 1.0

    def test_correct_slow_answer_medium_confidence(self):
        result = self.calc.compute(
            is_correct=True,
            response_time_seconds=90.0,
            hints_used=0,
            retry_count=0,
            difficulty=1,
        )
        assert result.classification in ("medium", "low")

    def test_wrong_fast_answer_low_confidence(self):
        result = self.calc.compute(
            is_correct=False,
            response_time_seconds=5.0,
            hints_used=0,
            retry_count=0,
            difficulty=1,
        )
        assert result.score < 0.5
        assert result.factors.correctness_signal == 0.0

    def test_wrong_slow_answer_low_confidence(self):
        result = self.calc.compute(
            is_correct=False,
            response_time_seconds=120.0,
            hints_used=3,
            retry_count=2,
            difficulty=1,
        )
        assert result.classification == "low"
        assert result.score < 0.3

    def test_max_hints_penalty(self):
        no_hints = self.calc.compute(True, 15.0, hints_used=0, difficulty=2)
        many_hints = self.calc.compute(True, 15.0, hints_used=5, difficulty=2)
        assert no_hints.score > many_hints.score
        assert many_hints.factors.hint_penalty > 0

    def test_max_retries_penalty(self):
        no_retries = self.calc.compute(True, 15.0, retry_count=0, difficulty=2)
        many_retries = self.calc.compute(True, 15.0, retry_count=4, difficulty=2)
        assert no_retries.score > many_retries.score
        assert many_retries.factors.retry_penalty > 0

    def test_recurrence_penalty(self):
        no_recur = self.calc.compute(True, 15.0, difficulty=2, is_recurrence=False)
        recur = self.calc.compute(True, 15.0, difficulty=2, is_recurrence=True)
        assert no_recur.score > recur.score
        assert recur.factors.recurrence_penalty > 0

    def test_difficulty_boost_on_correct(self):
        easy = self.calc.compute(True, 15.0, difficulty=1)
        hard = self.calc.compute(True, 15.0, difficulty=5)
        assert hard.score >= easy.score
        assert hard.factors.difficulty_boost > easy.factors.difficulty_boost

    def test_no_boost_on_wrong_regardless_of_difficulty(self):
        result = self.calc.compute(False, 30.0, difficulty=5)
        assert result.factors.difficulty_boost == 0.0

    def test_score_clamped_to_zero(self):
        result = self.calc.compute(
            is_correct=False,
            response_time_seconds=200.0,
            hints_used=5,
            retry_count=5,
            difficulty=1,
            is_recurrence=True,
        )
        assert 0.0 <= result.score <= 1.0

    def test_score_clamped_to_one(self):
        result = self.calc.compute(
            is_correct=True,
            response_time_seconds=1.0,
            hints_used=0,
            retry_count=0,
            difficulty=5,
        )
        assert result.score <= 1.0

    def test_all_factors_present_in_result(self):
        result = self.calc.compute(True, 20.0, hints_used=1, retry_count=0, difficulty=3)
        assert isinstance(result, QConfResult)
        assert isinstance(result.factors, ConfidenceFactors)
        assert result.factors.correctness_signal >= 0
        assert result.factors.time_factor >= 0
        assert result.factors.hint_penalty >= 0
        assert result.factors.retry_penalty >= 0
        assert result.factors.difficulty_boost >= 0
        assert result.factors.recurrence_penalty >= 0
        assert result.classification in ("high", "medium", "low")

    def test_correct_very_fast_max_difficulty(self):
        result = self.calc.compute(
            is_correct=True,
            response_time_seconds=2.0,
            hints_used=0,
            retry_count=0,
            difficulty=5,
        )
        assert result.classification == "high"
        assert result.score >= 0.80

    def test_custom_weights(self):
        custom_weights = ConfidenceWeights(
            correctness=0.8, response_time=0.1, hints=0.05, retries=0.03, difficulty=0.02
        )
        calc = ConfidenceCalculator(weights=custom_weights)
        result = calc.compute(True, 15.0)
        assert 0.0 <= result.score <= 1.0

    def test_custom_thresholds(self):
        thresholds = ConfidenceThresholds(high_confidence=0.9, medium_confidence=0.5)
        calc = ConfidenceCalculator(thresholds=thresholds)
        result = calc.compute(True, 10.0, difficulty=3)
        assert result.classification in ("high", "medium", "low")

    def test_correct_expected_time_boundary(self):
        result = self.calc.compute(
            is_correct=True,
            response_time_seconds=25.0,
            hints_used=0,
            retry_count=0,
            difficulty=1,
        )
        assert 0.0 <= result.score <= 1.0

    def test_negative_values_not_allowed(self):
        result = self.calc.compute(
            is_correct=True,
            response_time_seconds=0.0,
            hints_used=0,
            retry_count=0,
            difficulty=1,
        )
        assert result.score >= 0
        assert result.factors.time_factor <= 1.0

    def test_zero_difficulty_defaults_to_min(self):
        result = self.calc.compute(True, 15.0, difficulty=1)
        score_d1 = result.score
        result = self.calc.compute(True, 15.0, difficulty=0)
        score_d0 = result.score
        assert score_d0 <= score_d1


class TestConfidenceService:
    def setup_method(self):
        self.service = ConfidenceService()

    def test_compute_confidence_delegates_to_calculator(self):
        result = self.service.compute_confidence(
            is_correct=True,
            response_time_seconds=12.0,
            hints_used=0,
            retry_count=0,
            difficulty=2,
        )
        assert isinstance(result, QConfResult)
        assert 0.0 <= result.score <= 1.0

    def test_service_with_custom_calculator(self):
        calc = ConfidenceCalculator()
        service = ConfidenceService(calculator=calc)
        result = service.compute_confidence(True, 10.0)
        assert isinstance(result, QConfResult)

    def test_service_produces_classification(self):
        result = self.service.compute_confidence(True, 8.0, difficulty=3)
        assert result.classification in ("high", "medium", "low")


class TestConfidenceAnalytics:
    def setup_method(self):
        self.calc = ConfidenceCalculator()
        self.analytics = ConfidenceAnalytics()

    def _results(self, count=5):
        return [
            self.calc.compute(True, 10.0, difficulty=3),
            self.calc.compute(True, 15.0, difficulty=2),
            self.calc.compute(True, 25.0, difficulty=1),
            self.calc.compute(False, 30.0, difficulty=2),
            self.calc.compute(False, 5.0, difficulty=1),
        ][:count]

    def test_classify_batch_returns_counts(self):
        results = self._results()
        counts = self.analytics.classify_batch(results)
        assert "high" in counts
        assert "medium" in counts
        assert "low" in counts
        assert sum(counts.values()) == len(results)

    def test_average_confidence(self):
        results = self._results()
        avg = self.analytics.average_confidence(results)
        assert 0.0 <= avg <= 1.0

    def test_average_confidence_empty(self):
        assert self.analytics.average_confidence([]) == 0.0

    def test_confidence_distribution(self):
        results = self._results()
        dist = self.analytics.confidence_distribution(results)
        assert "high" in dist
        assert "medium" in dist
        assert "low" in dist
        total = sum(dist.values())
        assert abs(total - 100.0) < 0.1 or total == 0

    def test_confidence_distribution_empty(self):
        dist = self.analytics.confidence_distribution([])
        assert dist["high"] == 0.0
        assert dist["medium"] == 0.0
        assert dist["low"] == 0.0

    def test_compute_mastery_adjustment_high(self):
        adj = self.analytics.compute_mastery_adjustment(0.70)
        assert adj == 0.05

    def test_compute_mastery_adjustment_medium(self):
        adj = self.analytics.compute_mastery_adjustment(0.60)
        assert adj == 0.0

    def test_compute_mastery_adjustment_low(self):
        adj = self.analytics.compute_mastery_adjustment(0.30)
        assert adj == -0.05

    def test_get_qconf_summary(self):
        results = self._results()
        summary = self.analytics.get_qconf_summary(results)
        assert "average_confidence" in summary
        assert "distribution" in summary
        assert "high_count" in summary
        assert "medium_count" in summary
        assert "low_count" in summary
        assert "total_questions" in summary
        assert summary["total_questions"] == len(results)

    def test_get_qconf_summary_empty(self):
        summary = self.analytics.get_qconf_summary([])
        assert summary["average_confidence"] == 0.0
        assert summary["total_questions"] == 0

    def test_custom_thresholds(self):
        thresholds = ConfidenceThresholds(high_confidence=0.95, medium_confidence=0.7)
        analytics = ConfidenceAnalytics(thresholds=thresholds)
        adj = analytics.compute_mastery_adjustment(0.80)
        assert adj == 0.0


class TestConfidenceIntegration:
    def test_full_flow_correct_student(self):
        calc = ConfidenceCalculator()
        service = ConfidenceService(calculator=calc)
        analytics = ConfidenceAnalytics()

        results = []
        for _ in range(10):
            result = service.compute_confidence(
                is_correct=True,
                response_time_seconds=15.0,
                hints_used=0,
                retry_count=0,
                difficulty=3,
            )
            results.append(result)

        summary = analytics.get_qconf_summary(results)
        assert summary["average_confidence"] >= 0.5
        assert summary["high_count"] >= 0

    def test_full_flow_struggling_student(self):
        calc = ConfidenceCalculator()
        service = ConfidenceService(calculator=calc)
        analytics = ConfidenceAnalytics()

        results = []
        for is_correct in [False, False, True, False, True]:
            result = service.compute_confidence(
                is_correct=is_correct,
                response_time_seconds=60.0,
                hints_used=2,
                retry_count=1,
                difficulty=2,
            )
            results.append(result)

        summary = analytics.get_qconf_summary(results)
        assert summary["average_confidence"] >= 0.0

    def test_qconf_mastery_integration(self):
        calc = ConfidenceCalculator()
        analytics = ConfidenceAnalytics()

        high_qconf = calc.compute(True, 8.0, difficulty=4)
        low_qconf = calc.compute(False, 90.0, hints_used=3, retry_count=2, difficulty=1)

        high_adj = analytics.compute_mastery_adjustment(high_qconf.score)
        low_adj = analytics.compute_mastery_adjustment(low_qconf.score)

        assert high_adj >= low_adj
        assert low_adj in (-0.05, 0.0)
