import time

from studob.exceptions import RetrievalError
from studob.logging_setup import get_logger
from studob.student.session_memory import SessionMemoryService

logger = get_logger("retrieval.student_filter")


class StudentFilterModule:
    def __init__(self, session_memory: SessionMemoryService) -> None:
        self._session_memory = session_memory

    async def filter(
        self,
        student_id: str,
        session_id: str,
        candidates: list[dict],
    ) -> list[dict]:
        start = time.perf_counter()
        try:
            seen_ids = await self._session_memory.get_seen_question_ids(student_id, session_id)
            seen_set = set(seen_ids)
            filtered = [c for c in candidates if str(c.get("id", "")) not in seen_set]
            removed = len(candidates) - len(filtered)
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Student filter complete",
                extra={
                    "student_id": student_id,
                    "session_id": session_id,
                    "candidates_before": len(candidates),
                    "candidates_after": len(filtered),
                    "removed_seen": removed,
                    "duration_ms": elapsed,
                },
            )
            return filtered
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Student filter failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Student filter failed: {e}") from e
