from fastapi import APIRouter, Request

from studob.schemas.session import (
    AttemptCreate,
    AttemptResponse,
    SessionCreate,
    SessionResponse,
)

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(request: Request, data: SessionCreate):
    svc = request.app.state.context.session_memory
    return await svc.start_session(data.student_id, data.session_type)


@router.post("/{session_id}/attempts", response_model=AttemptResponse, status_code=201)
async def record_attempt(request: Request, session_id: str, data: AttemptCreate):
    svc = request.app.state.context.session_memory
    return await svc.record_attempt(session_id, data)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(request: Request, session_id: str):
    svc = request.app.state.context.session_memory
    return await svc.get_session(session_id)


@router.put("/{session_id}/end", response_model=SessionResponse)
async def end_session(request: Request, session_id: str):
    svc = request.app.state.context.session_memory
    return await svc.end_session(session_id)


@router.get("/student/{student_id}/active", response_model=list[SessionResponse])
async def get_active_sessions(request: Request, student_id: str):
    svc = request.app.state.context.session_memory
    return await svc.get_active_sessions(student_id)


@router.get("/student/{student_id}/all", response_model=list[SessionResponse])
async def get_student_sessions(request: Request, student_id: str):
    svc = request.app.state.context.session_memory
    return await svc.get_sessions_by_student(student_id)
