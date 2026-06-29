import time

from suraj_dada.exceptions import RetrievalError
from suraj_dada.logging_setup import get_logger

logger = get_logger("retrieval.mistake_matcher")


class MistakePatternMatcher:
    def __init__(self) -> None:
        pass

    async def match(
        self,
        candidates: list[dict],
        error_category: str,
        concept_tag: str,
    ) -> list[dict]:
        start = time.perf_counter()
        try:
            scored = []
            for c in candidates:
                score = 0.0
                tags = c.get("tags") or []
                topic = (c.get("topic") or "").lower()
                subtopic = (c.get("subtopic") or "").lower()
                concept_lower = concept_tag.lower()
                error_lower = error_category.lower()

                if concept_lower in topic or concept_lower in subtopic:
                    score += 0.5
                if error_lower in topic or error_lower in subtopic:
                    score += 0.3
                if any(concept_lower in (t.lower() or "") for t in tags):
                    score += 0.2
                if any(error_lower in (t.lower() or "") for t in tags):
                    score += 0.2

                scored.append({**c, "relevance_score": round(min(score, 1.0), 4)})

            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Mistake matching complete",
                extra={
                    "candidates": len(scored),
                    "error_category": error_category,
                    "concept_tag": concept_tag,
                    "duration_ms": elapsed,
                },
            )
            return scored
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Mistake matching failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Mistake matching failed: {e}") from e
