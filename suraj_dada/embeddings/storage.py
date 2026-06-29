import os
import pickle

import faiss
import numpy as np

from suraj_dada.exceptions import EmbeddingError
from suraj_dada.logging_setup import get_logger

logger = get_logger("embeddings.storage")


class VectorStoreService:
    def __init__(self, dimension: int = 384, index_path: str | None = None):
        self._dimension = dimension
        self._index_path = index_path
        self._next_id = 0
        self._metadata: dict[int, dict] = {}
        self._index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
        if index_path is not None and os.path.exists(index_path):
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.load())
                else:
                    loop.run_until_complete(self.load())
            except Exception:
                pass

    async def add_item(self, item_id: str, vector: list[float], metadata: dict) -> None:
        fid = self._next_id
        self._next_id += 1
        vec = np.array([vector], dtype=np.float32)
        faiss.normalize_L2(vec)
        ids = np.array([fid], dtype=np.int64)
        self._index.add_with_ids(vec, ids)
        self._metadata[fid] = {"id": item_id, **metadata}
        logger.debug("Added item to vector store", extra={"item_id": item_id, "faiss_id": fid})

    async def add_items(self, items: list[tuple[str, list[float], dict]]) -> None:
        n = len(items)
        if n == 0:
            return
        vectors = np.zeros((n, self._dimension), dtype=np.float32)
        ids = np.zeros(n, dtype=np.int64)
        for i, (item_id, vec, meta) in enumerate(items):
            vectors[i] = np.array(vec, dtype=np.float32)
            fid = self._next_id
            self._next_id += 1
            ids[i] = fid
            self._metadata[fid] = {"id": item_id, **meta}
        faiss.normalize_L2(vectors)
        self._index.add_with_ids(vectors, ids)
        logger.info("Added items to vector store", extra={"count": n})

    async def search(self, query_vector: list[float], top_k: int = 10) -> list[dict]:
        if self._index.ntotal == 0:
            return []
        vec = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(vec)
        distances, indices = self._index.search(vec, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0], strict=False):
            if idx == -1:
                continue
            meta = self._metadata.get(int(idx), {})
            results.append(
                {
                    "id": meta.get("id", str(idx)),
                    "score": float(dist),
                    "metadata": meta,
                }
            )
        return results

    async def search_with_filter(
        self, query_vector: list[float], top_k: int, allowed_ids: set[str]
    ) -> list[dict]:
        if self._index.ntotal == 0:
            return []
        all_results = await self.search(query_vector, top_k=max(top_k * 5, 100))
        filtered = [r for r in all_results if r.get("id") in allowed_ids]
        return filtered[:top_k]

    async def remove_item(self, item_id: str) -> None:
        to_remove = [fid for fid, meta in self._metadata.items() if meta.get("id") == item_id]
        if not to_remove:
            logger.warning("Item not found in vector store", extra={"item_id": item_id})
            return
        ids_to_remove = np.array(to_remove, dtype=np.int64)
        self._index.remove_ids(ids_to_remove)
        for fid in to_remove:
            del self._metadata[fid]
        logger.debug("Removed item from vector store", extra={"item_id": item_id})

    async def get_item_count(self) -> int:
        return self._index.ntotal

    async def save(self) -> None:
        if self._index_path is None:
            logger.warning("No index_path set, skipping save")
            return
        os.makedirs(os.path.dirname(self._index_path), exist_ok=True)
        faiss.write_index(self._index, self._index_path)
        meta_path = self._index_path + ".meta"
        with open(meta_path, "wb") as f:
            pickle.dump({"metadata": self._metadata, "next_id": self._next_id}, f)
        logger.info(
            "Vector store saved", extra={"path": self._index_path, "count": self._index.ntotal}
        )

    async def load(self) -> None:
        if self._index_path is None or not os.path.exists(self._index_path):
            logger.warning("No index file to load")
            return
        try:
            self._index = faiss.read_index(self._index_path)
            meta_path = self._index_path + ".meta"
            if os.path.exists(meta_path):
                with open(meta_path, "rb") as f:
                    data = pickle.load(f)
                    self._metadata = data.get("metadata", {})
                    self._next_id = data.get("next_id", self._index.ntotal)
            logger.info(
                "Vector store loaded", extra={"path": self._index_path, "count": self._index.ntotal}
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to load vector index: {e}") from e
