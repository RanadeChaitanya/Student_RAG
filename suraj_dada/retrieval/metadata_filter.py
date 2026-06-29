import time

from suraj_dada.exceptions import RetrievalError
from suraj_dada.logging_setup import get_logger
from suraj_dada.question_bank.metadata import MetadataFilterService
from suraj_dada.schemas.question import MetadataFilterResult, QuestionFilter

logger = get_logger("retrieval.metadata_filter")


class MetadataFilterModule:
    def __init__(self, filter_service: MetadataFilterService) -> None:
        self._filter_service = filter_service

    async def filter(
        self,
        subject: str,
        topic: str | None = None,
        subtopic: str | None = None,
        difficulty_band: tuple[int, int] = (1, 5),
        exclude_ids: list[str] | None = None,
    ) -> MetadataFilterResult:
        start = time.perf_counter()
        try:
            qf = QuestionFilter(
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                difficulty_min=difficulty_band[0],
                difficulty_max=difficulty_band[1],
            )
            result = await self._filter_service.filter_by_criteria(
                filters=qf, exclude_ids=exclude_ids
            )
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Metadata filter complete",
                extra={
                    "subject": subject,
                    "topic": topic,
                    "subtopic": subtopic,
                    "difficulty_band": str(difficulty_band),
                    "matched": result.total_count,
                    "duration_ms": elapsed,
                },
            )
            return result
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Metadata filter failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Metadata filter failed: {e}") from e
