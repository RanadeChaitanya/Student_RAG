import json

from suraj_dada.exceptions import LlmError
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.practice import PracticeQuestion

logger = get_logger("llm.output_parser")


class OutputParser:
    async def parse_practice_session(self, llm_output: str) -> list[PracticeQuestion]:
        try:
            data = json.loads(llm_output)
        except json.JSONDecodeError as exc:
            raise LlmError(
                "Failed to parse LLM output as JSON",
                details={"raw_output": llm_output[:500], "error": str(exc)},
            ) from exc

        questions_data = data.get("questions", data if isinstance(data, list) else [])
        if isinstance(questions_data, dict):
            questions_data = [questions_data]

        if not questions_data:
            raise LlmError(
                "No questions found in LLM output",
                details={"raw_output": llm_output[:500]},
            )

        questions = []
        for i, q in enumerate(questions_data):
            try:
                question = PracticeQuestion(
                    id=q.get("id", i + 1),
                    question_text=q.get("question_text", ""),
                    options=q.get("options"),
                    difficulty=q.get("difficulty", 3),
                    hint=q.get("hint"),
                    concept_reference=q.get("concept_reference"),
                )
                questions.append(question)
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning(
                    "Skipping malformed question in LLM output",
                    extra={"index": i, "error": str(exc), "data": q},
                )
                continue

        if not questions:
            raise LlmError(
                "All questions in LLM output were malformed",
                details={"raw_output": llm_output[:500]},
            )

        logger.info("Parsed practice session", extra={"question_count": len(questions)})
        return questions

    async def parse_explanation(self, llm_output: str) -> str:
        cleaned = llm_output.strip()
        if not cleaned:
            raise LlmError("Empty explanation from LLM", details={"raw_output": llm_output})
        logger.info("Parsed explanation", extra={"length": len(cleaned)})
        return cleaned

    async def parse_hint(self, llm_output: str) -> str:
        cleaned = llm_output.strip()
        if not cleaned:
            raise LlmError("Empty hint from LLM", details={"raw_output": llm_output})
        logger.info("Parsed hint", extra={"length": len(cleaned)})
        return cleaned
