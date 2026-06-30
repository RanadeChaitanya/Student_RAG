import time

from studob.exceptions import RetrievalError
from studob.graph.service import ConceptGraphService
from studob.logging_setup import get_logger

logger = get_logger("retrieval.concept_expansion")


class ConceptExpansionModule:
    def __init__(self, graph_service: ConceptGraphService) -> None:
        self._graph_service = graph_service

    async def expand(self, concept_ids: list[str]) -> list[dict]:
        start = time.perf_counter()
        try:
            expanded = await self._graph_service.expand_concepts(concept_ids)
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Concept expansion complete",
                extra={
                    "input_count": len(concept_ids),
                    "expanded_count": len(expanded),
                    "duration_ms": elapsed,
                },
            )
            result = []
            for node in expanded:
                result.append(
                    {
                        "id": node.get("id"),
                        "display_name": node.get("display_name"),
                        "subject": node.get("subject"),
                        "topic": node.get("topic"),
                        "subtopic": node.get("subtopic"),
                        "difficulty": node.get("difficulty"),
                    }
                )
            return result
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Concept expansion failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Concept expansion failed: {e}") from e
