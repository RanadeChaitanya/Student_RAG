

from studob.logging_setup import get_logger

logger = get_logger("content_engine.solution_repository")


class SolutionRepository:
    def __init__(self) -> None:
        self._solutions: dict[int, list[str]] = {}

    def store_solution(self, question_id: int, steps: list[str]) -> None:
        self._solutions[question_id] = steps

    def get_solution(self, question_id: int) -> list[str] | None:
        return self._solutions.get(question_id)

    def build_from_explanation(self, question_id: int, explanation: str) -> list[str]:
        sentences = [s.strip() for s in explanation.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        steps = []
        for i, sentence in enumerate(sentences[:5]):
            steps.append(f"Step {i + 1}: {sentence}")
        if not steps:
            steps.append("Review the concept and try the problem again.")
        self._solutions[question_id] = steps
        return steps
