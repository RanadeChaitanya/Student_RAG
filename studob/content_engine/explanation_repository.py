

from studob.logging_setup import get_logger

logger = get_logger("content_engine.explanation_repository")


class ExplanationRepository:
    def __init__(self) -> None:
        self._explanations: dict[int, dict[str, str]] = {}

    def load_question_explanations(self, question_id: int, explanation: str) -> None:
        variants = self._generate_variants(explanation)
        self._explanations[question_id] = variants

    def _generate_variants(self, explanation: str) -> dict[str, str]:
        sentences = [s.strip() for s in explanation.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        return {
            "quick": sentences[0] if sentences else explanation,
            "detailed": explanation,
            "formula_derivation": self._build_from_sentences(sentences, "Formula derivation: "),
            "worked_example": explanation,
            "revision_summary": self._build_from_sentences(sentences, "Key point: "),
            "exam_strategy": self._build_exam_strategy(sentences),
        }

    def _build_from_sentences(self, sentences: list[str], prefix: str) -> str:
        if not sentences:
            return f"{prefix}No content available."
        return prefix + ". ".join(sentences)

    def _build_exam_strategy(self, sentences: list[str]) -> str:
        if not sentences:
            return "Carefully read the question and eliminate obviously wrong options first."
        return f"Exam tip: Focus on understanding why the correct answer is right. {sentences[0]}"

    def get_explanation(self, question_id: int, variant: str = "detailed") -> str | None:
        variants = self._explanations.get(question_id)
        if not variants:
            return None
        return variants.get(variant, variants.get("detailed"))

    def get_all_variants(self, question_id: int) -> dict[str, str]:
        return self._explanations.get(question_id, {})
