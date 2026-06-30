from studob.config.loader import Settings
from studob.content_engine.adaptive_renderer import AdaptiveRenderer
from studob.content_engine.explanation_repository import ExplanationRepository
from studob.content_engine.formula_repository import FormulaRepository
from studob.content_engine.hint_repository import HintRepository
from studob.content_engine.misconception_repository import MisconceptionRepository
from studob.content_engine.practice_selector import PracticeSelector, SelectedQuestion
from studob.content_engine.solution_repository import SolutionRepository
from studob.graph.service import ConceptGraphService
from studob.question_bank.app_questions import AppQuestionService
from studob.student.mastery import MasteryService


class ContentEngineService:
    def __init__(
        self,
        app_questions: AppQuestionService,
        mastery: MasteryService,
        concept_graph: ConceptGraphService,
        config: Settings,
    ) -> None:
        self.hint_repo = HintRepository()
        self.explanation_repo = ExplanationRepository()
        self.solution_repo = SolutionRepository()
        self.misconception_repo = MisconceptionRepository()
        self.formula_repo = FormulaRepository()
        self.adaptive_renderer = AdaptiveRenderer(
            hint_repo=self.hint_repo,
            explanation_repo=self.explanation_repo,
            solution_repo=self.solution_repo,
            misconception_repo=self.misconception_repo,
            formula_repo=self.formula_repo,
        )
        self.practice_selector = PracticeSelector(
            app_questions=app_questions,
            mastery=mastery,
            concept_graph=concept_graph,
            misconception_repo=self.misconception_repo,
            config=config,
        )
        self._app_questions = app_questions

    async def initialize(self) -> None:
        questions = await self._app_questions.get_all_questions()
        for q in questions:
            self.hint_repo.load_question_hints(q.id, q.question_text, q.explanation, q.options)
            self.explanation_repo.load_question_explanations(q.id, q.explanation)
            self.solution_repo.store_solution(q.id, q.explanation)

    def get_hint(self, question_id: int, hint_level: int, mastery_score: float) -> str | None:
        return self.adaptive_renderer.get_hint(question_id, hint_level, mastery_score)

    def get_explanation(self, question_id: int, mastery_score: float) -> str:
        return self.adaptive_renderer.get_explanation_variant(question_id, mastery_score)

    def get_content_package(self, question_id: int, concept_tag: str, mastery_score: float) -> dict:
        return self.adaptive_renderer.get_content_package(question_id, concept_tag, mastery_score)


__all__ = [
    "ContentEngineService",
    "HintRepository",
    "ExplanationRepository",
    "SolutionRepository",
    "MisconceptionRepository",
    "FormulaRepository",
    "AdaptiveRenderer",
    "PracticeSelector",
    "SelectedQuestion",
]
