from fastapi import APIRouter, Request

from suraj_dada.schemas.analytics import StudentAnalyticsResponse

router = APIRouter()


@router.get("/student/{student_id}", response_model=StudentAnalyticsResponse)
async def get_student_analytics(request: Request, student_id: str):
    svc = request.app.state.context.analytics
    return await svc.get_student_analytics(student_id)


@router.get("/session/{session_id}")
async def get_session_analytics(request: Request, session_id: str):
    svc = request.app.state.context.analytics
    return await svc.get_session_analytics(session_id)
