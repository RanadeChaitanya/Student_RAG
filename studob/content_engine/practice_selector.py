from dataclasses import dataclass, field

from studob.config.loader import Settings
from studob.content_engine.misconception_repository import MisconceptionRepository
from studob.graph.service import ConceptGraphService
from studob.logging_setup import get_logger
from studob.question_bank.app_questions import AppQuestionService
from studob.student.mastery import MasteryService

logger = get_logger("content_engine.practice_selector")


@dataclass
class SelectedQuestion:
    id: int
    question_text: str
    options: dict | None
    difficulty: int
    concept_tag: str
    subject: str = ""
    topic: str = ""
    correct_answer: str = ""


@dataclass
class PracticeSession:
    session_id: str
    student_id: str
    target_concept: str
    questions: list[SelectedQuestion] = field(default_factory=list)
    difficulty_progression: str = "adaptive"


class PracticeSelector:
    def __init__(
        self,
        app_questions: AppQuestionService,
        mastery: MasteryService,
        concept_graph: ConceptGraphService,
        misconception_repo: MisconceptionRepository,
        config: Settings,
    ) -> None:
        self._app_questions = app_questions
        self._mastery = mastery
        self._concept_graph = concept_graph
        self._misconception_repo = misconception_repo
        self._config = config

    async def select_questions(
        self,
        student_id: str,
        target_concept: str,
        question_count: int = 5,
        difficulty_band: str = "adaptive",
    ) -> list[SelectedQuestion]:
        weak_topics = await self._mastery.identify_weak_topics(student_id)

        related = await self._concept_graph.get_related_concepts(target_concept)
        all_concepts = [target_concept] + [r.get("id", "") for r in (related or [])]
        all_concepts = [c for c in all_concepts if c]

        difficulty_low, difficulty_high = 1, 5
        if difficulty_band == "easy":
            difficulty_low, difficulty_high = 1, 2
        elif difficulty_band == "medium":
            difficulty_low, difficulty_high = 3, 4
        elif difficulty_band == "hard":
            difficulty_low, difficulty_high = 4, 5
        elif difficulty_band == "adaptive":
            for wt in weak_topics:
                if target_concept.lower() in wt.subtopic.lower():
                    score = wt.score
                    if score < 30:
                        difficulty_low, difficulty_high = 1, 2
                    elif score < 50:
                        difficulty_low, difficulty_high = 1, 3
                    elif score < 70:
                        difficulty_low, difficulty_high = 2, 4
                    else:
                        difficulty_low, difficulty_high = 3, 5
                    break

        concept_map = await self._app_questions.get_questions_by_concepts_batch(
            all_concepts, difficulty_low, difficulty_high
        )

        questions = []
        for concept in all_concepts:
            for q in concept_map.get(concept, []):
                questions.append(
                    SelectedQuestion(
                        id=q.id,
                        question_text=q.question_text,
                        options=q.options,
                        difficulty=q.difficulty,
                        concept_tag=concept,
                        subject=q.subject,
                        topic=q.topic,
                        correct_answer=q.correct_answer,
                    )
                )

        questions.sort(key=lambda q: (
            0 if q.concept_tag.lower() == target_concept.lower() else 1,
            q.difficulty,
        ))

        selected = questions[:question_count]
        return selected
