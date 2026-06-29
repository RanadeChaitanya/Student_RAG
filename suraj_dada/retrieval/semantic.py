import time

from suraj_dada.embeddings.service import EmbeddingService
from suraj_dada.exceptions import RetrievalError
from suraj_dada.logging_setup import get_logger

logger = get_logger("retrieval.semantic")


class SemanticRetrievalModule:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._embedding_service = embedding_service

    async def retrieve(
        self,
        query_text: str,
        top_k: int,
        allowed_ids: set[str] | None = None,
    ) -> list[dict]:
        start = time.perf_counter()
        try:
            if allowed_ids is not None:
                results = await self._embedding_service.search_similar_filtered(
                    query_text=query_text, top_k=top_k, allowed_ids=allowed_ids
                )
            else:
                results = await self._embedding_service.search_similar(
                    query_text=query_text, top_k=top_k
                )
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Semantic retrieval complete",
                extra={
                    "top_k": top_k,
                    "filtered": allowed_ids is not None,
                    "results": len(results),
                    "duration_ms": elapsed,
                },
            )
            return results
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Semantic retrieval failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Semantic retrieval failed: {e}") from e
