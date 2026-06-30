
from studob.logging_setup import get_logger

logger = get_logger("content_engine.hint_repository")


class HintRepository:
    def __init__(self) -> None:
        self._hints: dict[int, list[str]] = {}
        self._solutions: dict[int, str] = {}

    def load_question_hints(self, question_id: int, question_text: str, explanation: str, options: dict | None = None) -> None:
        hints = self._generate_hints(question_text, explanation, options)
        self._hints[question_id] = hints

    def _generate_hints(self, question_text: str, explanation: str, options: dict | None = None) -> list[str]:
        sentences = [s.strip() for s in explanation.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        hints = []
        for i, sentence in enumerate(sentences[:3]):
            hint_num = i + 1
            hints.append(f"Hint {hint_num}: {sentence}")
        if not hints:
            hints.append("Review the relevant concept and try again.")
        return hints

    def get_hint(self, question_id: int, hint_level: int) -> str | None:
        hints = self._hints.get(question_id)
        if not hints:
            return None
        if hint_level <= 0 or hint_level > len(hints):
            return hints[-1]
        return hints[hint_level - 1]

    def get_all_hints(self, question_id: int) -> list[str]:
        return self._hints.get(question_id, [])

    def get_solution(self, question_id: int) -> str | None:
        return self._solutions.get(question_id)

    def store_solution(self, question_id: int, solution: str) -> None:
        self._solutions[question_id] = solution
