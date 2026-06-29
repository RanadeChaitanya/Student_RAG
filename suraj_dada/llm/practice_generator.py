from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from suraj_dada.config.loader import Settings, get_config
from suraj_dada.llm.client import LlmClient
from suraj_dada.llm.output_parser import OutputParser
from suraj_dada.llm.prompts import (
    EXPLANATION_PROMPT,
    HINT_PROMPT,
    PRACTICE_GENERATION_PROMPT,
)
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.practice import (
    PracticeQuestion,
    PracticeSessionRequest,
    PracticeSessionResponse,
)
from suraj_dada.schemas.retrieval import ContextPackage

logger = get_logger("llm.practice_generator")


class PracticeGenerator(ABC):
    @abstractmethod
    async def generate(
        self, request: PracticeSessionRequest, context: ContextPackage
    ) -> PracticeSessionResponse: ...

    @abstractmethod
    async def generate_hint(self, question_id: str, student_context: dict) -> str: ...

    @abstractmethod
    async def generate_explanation(self, question_id: str, student_context: dict) -> str: ...


class MockPracticeGenerator(PracticeGenerator):
    def __init__(self, config: Settings | None = None):
        self._config = config or get_config()
        self._generation_count = 0

    async def generate(
        self, request: PracticeSessionRequest, context: ContextPackage
    ) -> PracticeSessionResponse:
        self._generation_count += 1
        logger.info(
            "MockPracticeGenerator.generate called",
            extra={
                "generation_count": self._generation_count,
                "student_id": request.student_id,
                "target_concept": request.target_concept,
                "question_count": request.question_count,
            },
        )

        retrieved = context.retrieved_questions or []
        sorted_questions = sorted(retrieved, key=lambda q: q.difficulty)

        questions: list[PracticeQuestion] = []
        for item in sorted_questions[: request.question_count]:
            hint = f"Review the formula for {item.topic}"
            questions.append(
                PracticeQuestion(
                    id=item.question_id,
                    question_text=item.question_text,
                    options=item.options,
                    difficulty=item.difficulty,
                    hint=hint,
                    concept_reference=f"{item.subject}/{item.topic}/{item.subtopic}",
                )
            )

        if not questions:
            for i in range(request.question_count):
                questions.append(
                    PracticeQuestion(
                        id=i + 1,
                        question_text=f"Sample {request.target_concept} question {i + 1}",
                        options={
                            "A": "Option A",
                            "B": "Option B",
                            "C": "Option C",
                            "D": "Option D",
                        },
                        difficulty=(i % 5) + 1,
                        hint=f"Review the formula for {request.target_concept}",
                        concept_reference=request.target_concept,
                    )
                )

        return PracticeSessionResponse(
            practice_session_id=request.session_id,
            student_id=request.student_id,
            target_concept=request.target_concept,
            questions=questions,
            difficulty_progression="low_to_high",
            created_at=datetime.now(UTC),
        )

    async def generate_hint(self, question_id: str, student_context: dict) -> str:
        concept = student_context.get(
            "concept_reference", student_context.get("target_concept", "the topic")
        )
        logger.info(
            "MockPracticeGenerator.generate_hint",
            extra={"question_id": question_id, "concept": concept},
        )
        return f"Review the formula for {concept} and try breaking the problem into smaller steps."

    async def generate_explanation(self, question_id: str, student_context: dict) -> str:
        concept = student_context.get(
            "concept_reference", student_context.get("target_concept", "the topic")
        )
        correct_answer = student_context.get("correct_answer", "the correct answer")
        logger.info(
            "MockPracticeGenerator.generate_explanation",
            extra={"question_id": question_id, "concept": concept},
        )
        return f"The correct answer is {correct_answer} because it correctly applies the principles of {concept}."  # noqa: E501


class LlmPracticeGenerator(PracticeGenerator):
    def __init__(
        self,
        llm_client: LlmClient,
        output_parser: OutputParser,
        config: Settings | None = None,
    ):
        self._llm_client = llm_client
        self._output_parser = output_parser
        self._config = config or get_config()
        self._generation_count = 0

    def _render_prompt(self, template: str, context: ContextPackage, **extra: Any) -> str:
        return template.format(
            student_state=context.student_state,
            mistake_diagnosis=context.mistake_diagnosis,
            learning_objective=context.learning_objective,
            retrieved_questions=context.retrieved_questions,
            concept_notes="\n".join(context.concept_notes),
            formulas="\n".join(context.formulas),
            misconceptions="\n".join(context.misconceptions),
            session_memory=context.session_memory,
            **extra,
        )

    async def generate(
        self, request: PracticeSessionRequest, context: ContextPackage
    ) -> PracticeSessionResponse:
        self._generation_count += 1
        logger.info(
            "LlmPracticeGenerator.generate called",
            extra={
                "generation_count": self._generation_count,
                "student_id": request.student_id,
                "target_concept": request.target_concept,
            },
        )

        rendered = self._render_prompt(
            PRACTICE_GENERATION_PROMPT,
            context,
            question_count=request.question_count,
        )

        llm_output = await self._llm_client.generate(
            prompt=rendered,
            max_tokens=self._config.llm.max_output_tokens,
            temperature=self._config.llm.temperature,
        )

        questions = await self._output_parser.parse_practice_session(llm_output)

        return PracticeSessionResponse(
            practice_session_id=request.session_id,
            student_id=request.student_id,
            target_concept=request.target_concept,
            questions=questions,
            difficulty_progression="adaptive",
            created_at=datetime.now(UTC),
        )

    async def generate_hint(self, question_id: str, student_context: dict) -> str:
        logger.info("LlmPracticeGenerator.generate_hint", extra={"question_id": question_id})
        question_text = student_context.get("question_text", "")
        context = student_context.get("context")
        if context is None:
            context = ContextPackage(
                student_state={},
                mistake_diagnosis={},
                learning_objective="",
                retrieved_questions=[],
                concept_notes=[],
                formulas=[],
                misconceptions=[],
                session_memory={},
            )

        rendered = self._render_prompt(
            HINT_PROMPT,
            context,
            question_text=question_text,
        )

        llm_output = await self._llm_client.generate(
            prompt=rendered,
            max_tokens=512,
            temperature=0.5,
        )

        return await self._output_parser.parse_hint(llm_output)

    async def generate_explanation(self, question_id: str, student_context: dict) -> str:
        logger.info("LlmPracticeGenerator.generate_explanation", extra={"question_id": question_id})
        question_text = student_context.get("question_text", "")
        student_answer = student_context.get("student_answer", "")
        correct_answer = student_context.get("correct_answer", "")
        context = student_context.get("context")
        if context is None:
            context = ContextPackage(
                student_state={},
                mistake_diagnosis={},
                learning_objective="",
                retrieved_questions=[],
                concept_notes=[],
                formulas=[],
                misconceptions=[],
                session_memory={},
            )

        rendered = self._render_prompt(
            EXPLANATION_PROMPT,
            context,
            question_text=question_text,
            student_answer=student_answer,
            correct_answer=correct_answer,
        )

        llm_output = await self._llm_client.generate(
            prompt=rendered,
            max_tokens=1024,
            temperature=0.5,
        )

        return await self._output_parser.parse_explanation(llm_output)
