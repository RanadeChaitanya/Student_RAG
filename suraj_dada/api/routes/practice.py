from fastapi import APIRouter, Request

from suraj_dada.schemas.practice import (
    PracticeSessionRequest,
    PracticeSessionResponse,
    PracticeSessionResult,
)
from suraj_dada.schemas.retrieval import RetrievalRequest

router = APIRouter()


@router.post("/generate", response_model=PracticeSessionResponse)
async def generate_practice_session(request: Request, data: PracticeSessionRequest):
    retrieval = request.app.state.context.retrieval
    generator = request.app.state.context.practice_generator

    retrieval_req = RetrievalRequest(
        student_id=data.student_id,
        concept_tag=data.target_concept,
        error_category=data.error_category,
        session_id=data.session_id,
    )
    context = await retrieval.retrieve(retrieval_req)
    return await generator.generate(data, context)


@router.post("/{practice_session_id}/result", response_model=PracticeSessionResult)
async def submit_practice_result(request: Request, practice_session_id: str, data: dict):
    student_id = data.get("student_id")
    attempts_list = data.get("attempts", [])
    mastery_svc = request.app.state.context.mastery

    mastery_delta = 0.0
    for attempt in attempts_list:
        subtopic = attempt.get("subtopic", "")
        signals = {
            "correctness": 1.0 if attempt.get("is_correct") else 0.0,
            "response_time_ratio": min(attempt.get("response_time_seconds", 30) / 30.0, 2.0),
            "hints_used_count": attempt.get("hints_used", 0),
            "retry_count": attempt.get("retry_count", 0),
            "recurrence_flag": 1 if attempt.get("is_recurrence", False) else 0,
            "subject": attempt.get("subject", ""),
            "topic": attempt.get("topic", ""),
        }
        if subtopic:
            updated = await mastery_svc.update_mastery(student_id, subtopic, signals)
            mastery_delta = updated.score - mastery_delta if mastery_delta == 0.0 else updated.score

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
    generator = request.app.state.context.practice_generator
    student_context = {"question_id": question_id}
    hint = await generator.generate_hint(str(question_id), student_context)
    return {"question_id": question_id, "hint": hint}
