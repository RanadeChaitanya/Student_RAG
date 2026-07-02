from studob.confidence.constants import DEFAULT_THRESHOLDS, ConfidenceThresholds
from studob.confidence.models import QConfResult

HIGH_CONF = "high"
MEDIUM_CONF = "medium"
LOW_CONF = "low"


class ConfidenceAnalytics:
    def __init__(self, thresholds: ConfidenceThresholds | None = None):
        self._thresholds = thresholds or DEFAULT_THRESHOLDS

    def classify_batch(self, results: list[QConfResult]) -> dict[str, int]:
        counts = {HIGH_CONF: 0, MEDIUM_CONF: 0, LOW_CONF: 0}
        for r in results:
            if r.score >= self._thresholds.high_confidence:
                counts[HIGH_CONF] += 1
            elif r.score >= self._thresholds.medium_confidence:
                counts[MEDIUM_CONF] += 1
            else:
                counts[LOW_CONF] += 1
        return counts

    def average_confidence(self, results: list[QConfResult]) -> float:
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)

    def confidence_distribution(self, results: list[QConfResult]) -> dict[str, float]:
        total = len(results)
        if total == 0:
            return {HIGH_CONF: 0.0, MEDIUM_CONF: 0.0, LOW_CONF: 0.0}
        counts = self.classify_batch(results)
        return {
            HIGH_CONF: round(counts[HIGH_CONF] / total * 100, 1),
            MEDIUM_CONF: round(counts[MEDIUM_CONF] / total * 100, 1),
            LOW_CONF: round(counts[LOW_CONF] / total * 100, 1),
        }

    def compute_mastery_adjustment(self, qconf_score: float) -> float:
        if qconf_score >= self._thresholds.high_confidence:
            return 0.05
        elif qconf_score >= self._thresholds.medium_confidence:
            return 0.0
        else:
            return -0.05

    def get_qconf_summary(self, results: list[QConfResult]) -> dict:
        return {
            "average_confidence": round(self.average_confidence(results), 4),
            "distribution": self.confidence_distribution(results),
            "high_count": self.classify_batch(results).get(HIGH_CONF, 0),
            "medium_count": self.classify_batch(results).get(MEDIUM_CONF, 0),
            "low_count": self.classify_batch(results).get(LOW_CONF, 0),
            "total_questions": len(results),
        }
