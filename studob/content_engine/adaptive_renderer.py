from typing import Any

from studob.content_engine.explanation_repository import ExplanationRepository
from studob.content_engine.formula_repository import FormulaRepository
from studob.content_engine.hint_repository import HintRepository
from studob.content_engine.misconception_repository import MisconceptionRepository
from studob.content_engine.solution_repository import SolutionRepository
from studob.logging_setup import get_logger

logger = get_logger("content_engine.adaptive_renderer")


class AdaptiveRenderer:
    def __init__(
        self,
        hint_repo: HintRepository,
        explanation_repo: ExplanationRepository,
        solution_repo: SolutionRepository,
        misconception_repo: MisconceptionRepository,
        formula_repo: FormulaRepository,
    ) -> None:
        self._hint_repo = hint_repo
        self._explanation_repo = explanation_repo
        self._solution_repo = solution_repo
        self._misconception_repo = misconception_repo
        self._formula_repo = formula_repo

    def get_explanation_variant(self, question_id: int, mastery_score: float) -> str:
        if mastery_score < 40:
            variant = "quick"
        elif mastery_score < 60:
            variant = "detailed"
        elif mastery_score < 80:
            variant = "worked_example"
        else:
            variant = "exam_strategy"
        explanation = self._explanation_repo.get_explanation(question_id, variant)
        if explanation is None:
            explanation = self._explanation_repo.get_explanation(question_id, "detailed")
        return explanation or "No explanation available."

    def get_hint(self, question_id: int, hint_level: int, mastery_score: float) -> str | None:
        if mastery_score < 40 and hint_level > 1:
            return self._hint_repo.get_hint(question_id, min(hint_level, 2))
        return self._hint_repo.get_hint(question_id, hint_level)

    def get_content_package(self, question_id: int, concept_tag: str, mastery_score: float) -> dict[str, Any]:
        explanation = self.get_explanation_variant(question_id, mastery_score)
        formulas = self._formula_repo.get_formulas_for_concept(concept_tag)
        misconceptions = self._misconception_repo.get_misconceptions_for_concept(concept_tag)
        return {
            "question_id": question_id,
            "explanation": explanation,
            "formulas": formulas,
            "misconceptions": misconceptions,
        }
