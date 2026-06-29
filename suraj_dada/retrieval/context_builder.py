import time

from suraj_dada.exceptions import RetrievalError
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.retrieval import ContextPackage, RetrievedItem

logger = get_logger("retrieval.context_builder")


class ContextBuilder:
    def __init__(self) -> None:
        pass

    async def build(
        self,
        student_state: dict,
        mistake_diagnosis: dict,
        learning_objective: str,
        retrieved_questions: list[dict],
        concept_notes: list[dict],
        formulas: list[dict],
        misconceptions: list[dict],
        session_memory: dict,
    ) -> ContextPackage:
        start = time.perf_counter()
        try:
            if not learning_objective:
                raise RetrievalError("learning_objective is required for context building")
            if not retrieved_questions:
                raise RetrievalError("retrieved_questions list is empty")

            items = []
            for q in retrieved_questions:
                items.append(
                    RetrievedItem(
                        question_id=q.get("id") or q.get("question_id", 0),
                        subject=q.get("subject", ""),
                        topic=q.get("topic", ""),
                        subtopic=q.get("subtopic", ""),
                        difficulty=q.get("difficulty", 3),
                        question_text=q.get("question_text", ""),
                        options=q.get("options"),
                        explanation=q.get("explanation", ""),
                        relevance_score=q.get("combined_score") or q.get("relevance_score", 0.0),
                        source=q.get("source", "app"),
                    )
                )

            package = ContextPackage(
                student_state=student_state or {},
                mistake_diagnosis=mistake_diagnosis or {},
                learning_objective=learning_objective,
                retrieved_questions=items,
                concept_notes=[n.get("text", str(n)) for n in (concept_notes or [])],
                formulas=[f.get("text", str(f)) for f in (formulas or [])],
                misconceptions=[m.get("text", str(m)) for m in (misconceptions or [])],
                session_memory=session_memory or {},
            )

            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Context package built",
                extra={
                    "question_count": len(items),
                    "concept_notes_count": len(package.concept_notes),
                    "formulas_count": len(package.formulas),
                    "misconceptions_count": len(package.misconceptions),
                    "duration_ms": elapsed,
                },
            )
            return package
        except RetrievalError:
            raise
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Context building failed",
                extra={"error": str(e), "duration_ms": elapsed},
            )
            raise RetrievalError(f"Context building failed: {e}") from e
