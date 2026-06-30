import time

from studob.config.loader import Settings
from studob.exceptions import RetrievalError
from studob.logging_setup import get_logger

logger = get_logger("retrieval.reranker")


class CrossEncoderReranker:
    def __init__(self, config: Settings) -> None:
        self._config = config

    async def rerank(
        self,
        query_text: str,
        candidates: list[dict],
        top_k: int,
        target_difficulty: int = 3,
    ) -> list[dict]:
        start = time.perf_counter()
        try:
            scored = []
            query_lower = query_text.lower()
            for c in candidates:
                concept_score = 0.0
                topic = (c.get("topic") or "").lower()
                subtopic = (c.get("subtopic") or "").lower()
                if any(word in topic or word in subtopic for word in query_lower.split()):
                    concept_score = 0.8
                elif query_lower in topic or query_lower in subtopic:
                    concept_score = 1.0

                difficulty = c.get("difficulty", 3)
                target_diff = max(1, min(5, target_difficulty))
                diff_delta = 1.0 - min(abs(difficulty - target_diff) / 4.0, 1.0)

                mistake_score = c.get("relevance_score", 0.0)

                recency_penalty = 0.0
                if c.get("recency_penalty"):
                    recency_penalty = min(c["recency_penalty"], 1.0)

                combined = (
                    0.3 * concept_score
                    + 0.2 * diff_delta
                    + 0.3 * mistake_score
                    - 0.2 * recency_penalty
                )
                scored.append({**c, "combined_score": round(combined, 4)})

            scored.sort(key=lambda x: x["combined_score"], reverse=True)
            reranked = scored[:top_k]

            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Reranking complete",
                extra={
                    "candidates_in": len(candidates),
                    "candidates_out": len(reranked),
                    "top_k": top_k,
                    "duration_ms": elapsed,
                },
            )
            return reranked
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Reranking failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Reranking failed: {e}") from e
