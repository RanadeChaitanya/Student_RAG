import logging

from suraj_dada.embeddings.generator import EmbeddingGenerator
from suraj_dada.embeddings.storage import VectorStoreService
from suraj_dada.exceptions import EmbeddingError

logger = logging.getLogger("embeddings.service")


class EmbeddingService:
    def __init__(
        self,
        generator: EmbeddingGenerator,
        storage: VectorStoreService,
        logger: logging.Logger = logger,
    ):
        self._generator = generator
        self._storage = storage
        self._logger = logger

    async def embed_and_store(self, item_id: str, text: str, metadata: dict) -> None:
        try:
            vector = await self._generator.generate(text)
            await self._storage.add_item(item_id, vector, metadata)
            self._logger.info("Embedded and stored item", extra={"item_id": item_id})
        except Exception as e:
            self._logger.error(
                "Failed to embed and store item", extra={"item_id": item_id, "error": str(e)}
            )
            raise EmbeddingError(f"Failed to embed and store item {item_id}: {e}") from e

    async def embed_and_store_batch(self, items: list[tuple[str, str, dict]]) -> None:
        try:
            texts = [item[1] for item in items]
            vectors = await self._generator.generate_batch(texts)
            store_items = []
            for i, (item_id, _, meta) in enumerate(items):
                store_items.append((item_id, vectors[i], meta))
            await self._storage.add_items(store_items)
            self._logger.info("Embedded and stored batch", extra={"count": len(items)})
        except Exception as e:
            self._logger.error(
                "Failed to embed and store batch", extra={"count": len(items), "error": str(e)}
            )
            raise EmbeddingError(f"Failed to embed and store batch: {e}") from e

    async def search_similar(self, query_text: str, top_k: int = 10) -> list[dict]:
        try:
            vector = await self._generator.generate(query_text)
            results = await self._storage.search(vector, top_k=top_k)
            self._logger.debug(
                "Search similar completed", extra={"results": len(results), "top_k": top_k}
            )
            return results
        except Exception as e:
            self._logger.error("Search similar failed", extra={"error": str(e)})
            raise EmbeddingError(f"Search similar failed: {e}") from e

    async def search_similar_filtered(
        self, query_text: str, top_k: int, allowed_ids: set[str]
    ) -> list[dict]:
        try:
            vector = await self._generator.generate(query_text)
            results = await self._storage.search_with_filter(
                vector, top_k=top_k, allowed_ids=allowed_ids
            )
            self._logger.debug(
                "Search similar filtered completed", extra={"results": len(results), "top_k": top_k}
            )
            return results
        except Exception as e:
            self._logger.error("Search similar filtered failed", extra={"error": str(e)})
            raise EmbeddingError(f"Search similar filtered failed: {e}") from e
