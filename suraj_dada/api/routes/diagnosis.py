from fastapi import APIRouter, Query, Request

from suraj_dada.schemas.diagnosis import (
    MistakeDiagnosisRequest,
    MistakeDiagnosisResponse,
    MistakeRecordResponse,
)

router = APIRouter()


@router.post("/diagnose", response_model=MistakeDiagnosisResponse)
async def diagnose_mistake(request: Request, data: MistakeDiagnosisRequest):
    svc = request.app.state.context.diagnosis
    return await svc.diagnose(data)


@router.get("/student/{student_id}/history", response_model=list[MistakeRecordResponse])
async def get_mistake_history(
    request: Request,
    student_id: str,
    limit: int = Query(20, ge=1, le=100),
):
    svc = request.app.state.context.diagnosis
    return await svc.get_mistake_history(student_id, limit=limit)


@router.get("/student/{student_id}/patterns")
async def get_recurring_patterns(request: Request, student_id: str):
    svc = request.app.state.context.diagnosis
    return await svc.get_recurring_patterns(student_id)
