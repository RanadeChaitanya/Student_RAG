from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from studob.confidence import ConfidenceCalculator
from studob.content_engine import ContentEngineService
from studob.schemas.practice import (
    PracticeSessionRequest,
    PracticeSessionResponse,
    PracticeSessionResult,
    PracticeQuestion,
)

router = APIRouter()


def get_content_engine(request: Request) -> ContentEngineService:
    return request.app.state.context.content_engine


@router.post("/generate", response_model=PracticeSessionResponse)
async def generate_practice_session(
    request: Request,
    data: PracticeSessionRequest,
    content_engine: ContentEngineService = Depends(get_content_engine),
):
    questions = await content_engine.practice_selector.select_questions(
        student_id=data.student_id,
        target_concept=data.target_concept,
        question_count=data.question_count,
        difficulty_band=data.difficulty_band,
    )

    practice_questions = [
        PracticeQuestion(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            difficulty=q.difficulty,
            concept_reference=q.concept_tag,
        )
        for q in questions
    ]

    return PracticeSessionResponse(
        practice_session_id=data.session_id,
        student_id=data.student_id,
        target_concept=data.target_concept,
        questions=practice_questions,
        difficulty_progression=data.difficulty_band,
        created_at=datetime.now(timezone.utc),
    )


@router.post("/{practice_session_id}/result", response_model=PracticeSessionResult)
async def submit_practice_result(request: Request, practice_session_id: str, data: dict):
    student_id = data.get("student_id")
    attempts_list = data.get("attempts", [])
    mastery_svc = request.app.state.context.mastery
    session_memory = request.app.state.context.session_memory
    qconf_calculator = ConfidenceCalculator()

    mastery_delta = 0.0
    for attempt in attempts_list:
        subtopic = attempt.get("subtopic", "")
        is_correct = attempt.get("is_correct", False)

        qconf_result = qconf_calculator.compute(
            is_correct=is_correct,
            response_time_seconds=attempt.get("response_time_seconds", 30),
            hints_used=attempt.get("hints_used", 0),
            retry_count=attempt.get("retry_count", 0),
            difficulty=attempt.get("difficulty", 1),
            is_recurrence=attempt.get("is_recurrence", False),
        )

        signals = {
            "correctness": 1.0 if is_correct else 0.0,
            "response_time_ratio": min(attempt.get("response_time_seconds", 30) / 30.0, 2.0),
            "hints_used_count": attempt.get("hints_used", 0),
            "retry_count": attempt.get("retry_count", 0),
            "recurrence_flag": 1 if attempt.get("is_recurrence", False) else 0,
            "subject": attempt.get("subject", ""),
            "topic": attempt.get("topic", ""),
            "qconf_score": qconf_result.score,
        }
        if subtopic:
            updated = await mastery_svc.update_mastery(student_id, subtopic, signals)
            mastery_delta = updated.score - mastery_delta if mastery_delta == 0.0 else updated.score

    try:
        await session_memory.end_session(practice_session_id, mastery_delta=mastery_delta)
    except Exception:
        pass

    weak_topics = await mastery_svc.identify_weak_topics(student_id)
    weak_remaining = [f"{w.subject}/{w.topic}/{w.subtopic}" for w in weak_topics]

    return PracticeSessionResult(
        practice_session_id=practice_session_id,
        student_id=student_id,
        attempts=attempts_list,
        mastery_delta=mastery_delta,
        weak_topics_remaining=weak_remaining,
    )


@router.get("/hint/{question_id}")
async def get_hint(request: Request, question_id: int):
    content_engine: ContentEngineService = request.app.state.context.content_engine
    hint = content_engine.get_hint(question_id, hint_level=1, mastery_score=50.0)
    return {"question_id": question_id, "hint": hint}


@router.get("/explanation/{question_id}")
async def get_explanation(request: Request, question_id: int):
    content_engine: ContentEngineService = request.app.state.context.content_engine
    explanation = content_engine.get_explanation(question_id, mastery_score=50.0)
    return {"question_id": question_id, "explanation": explanation}
