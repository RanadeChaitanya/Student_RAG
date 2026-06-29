import pytest

from suraj_dada.embeddings.generator import EmbeddingGenerator
from suraj_dada.embeddings.service import EmbeddingService
from suraj_dada.embeddings.storage import VectorStoreService


class TestEmbeddingGenerator:
    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        gen = EmbeddingGenerator(dimension=64)
        emb = await gen.generate("test query")
        assert len(emb) == 64

    @pytest.mark.asyncio
    async def test_deterministic(self):
        gen = EmbeddingGenerator(dimension=64)
        e1 = await gen.generate("hello")
        e2 = await gen.generate("hello")
        assert e1 == e2

    @pytest.mark.asyncio
    async def test_different_inputs_different(self):
        gen = EmbeddingGenerator(dimension=64)
        e1 = await gen.generate("hello")
        e2 = await gen.generate("world")
        assert e1 != e2

    @pytest.mark.asyncio
    async def test_batch_generate(self):
        gen = EmbeddingGenerator(dimension=64)
        embs = await gen.generate_batch(["a", "b", "c"])
        assert len(embs) == 3
        assert all(len(e) == 64 for e in embs)

    @pytest.mark.asyncio
    async def test_dimension_configurable(self):
        gen = EmbeddingGenerator(dimension=128)
        emb = await gen.generate("test")
        assert len(emb) == 128


class TestVectorStore:
    @pytest.mark.asyncio
    async def test_add_and_search(self, tmp_path):
        store = VectorStoreService(dimension=64, index_path=str(tmp_path / "faiss_test.bin"))
        await store.add_items([("1", [0.1] * 64, {}), ("2", [0.9] * 64, {})])
        results = await store.search([0.1] * 64, top_k=2)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_empty_search(self, tmp_path):
        store = VectorStoreService(dimension=64, index_path=str(tmp_path / "empty.bin"))
        results = await store.search([0.1] * 64, top_k=5)
        assert len(results) == 0


class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_embed_and_search(self, tmp_path):
        gen = EmbeddingGenerator(dimension=64)
        store = VectorStoreService(dimension=64, index_path=str(tmp_path / "svc_test.bin"))
        svc = EmbeddingService(gen, store)
        await svc.embed_and_store("1", "test question about physics", {})
        results = await svc.search_similar("physics question", top_k=5)
        assert len(results) > 0
