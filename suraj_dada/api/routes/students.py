from fastapi import APIRouter, Request

from suraj_dada.schemas.student import (
    MasteryScoreResponse,
    MasterySummaryResponse,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
    WeakTopicInfo,
)

router = APIRouter()


@router.post("/", response_model=StudentResponse, status_code=201)
async def create_student(request: Request, data: StudentCreate):
    svc = request.app.state.context.student_profile
    return await svc.create_student(data)


@router.get("/", response_model=list[StudentResponse])
async def list_students(request: Request):
    svc = request.app.state.context.student_profile
    return await svc.list_students()


@router.get("/by-name/{name}", response_model=StudentResponse)
async def get_student_by_name(request: Request, name: str):
    svc = request.app.state.context.student_profile
    student = await svc.get_student_by_name(name)
    if student is None:
        from suraj_dada.exceptions import NotFoundError

        raise NotFoundError("Student", name)
    return student


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(request: Request, student_id: str):
    svc = request.app.state.context.student_profile
    return await svc.get_student(student_id)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(request: Request, student_id: str, data: StudentUpdate):
    svc = request.app.state.context.student_profile
    return await svc.update_student(student_id, data)


@router.delete("/{student_id}", status_code=204)
async def delete_student(request: Request, student_id: str):
    svc = request.app.state.context.student_profile
    await svc.delete_student(student_id)


@router.get("/{student_id}/mastery", response_model=MasterySummaryResponse)
async def get_mastery_summary(request: Request, student_id: str):
    svc = request.app.state.context.mastery
    return await svc.get_mastery_summary(student_id)


@router.get("/{student_id}/mastery/{subtopic}", response_model=MasteryScoreResponse)
async def get_subtopic_mastery(request: Request, student_id: str, subtopic: str):
    svc = request.app.state.context.mastery
    return await svc.get_mastery(student_id, subtopic)


@router.get("/{student_id}/weak-topics", response_model=list[WeakTopicInfo])
async def get_weak_topics(request: Request, student_id: str):
    svc = request.app.state.context.mastery
    return await svc.identify_weak_topics(student_id)
