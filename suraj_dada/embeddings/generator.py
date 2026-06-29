import asyncio
import hashlib
import struct

from suraj_dada.logging_setup import get_logger

logger = get_logger("embeddings.generator")


class EmbeddingGenerator:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    async def generate(self, text: str) -> list[float]:
        result = [0.0] * self.dimension
        for i in range(self.dimension):
            h = hashlib.sha256(f"{text}:{i}".encode()).digest()
            (val,) = struct.unpack("I", h[:4])
            result[i] = (val / 4294967295.0) * 2 - 1
        magnitude = sum(v * v for v in result) ** 0.5
        if magnitude > 0:
            result = [v / magnitude for v in result]
        return result

    async def generate_batch(self, texts: list[str]) -> list[list[float]]:
        tasks = [self.generate(t) for t in texts]
        results = await asyncio.gather(*tasks)
        logger.debug("Generated embeddings batch", extra={"count": len(texts)})
        return results
