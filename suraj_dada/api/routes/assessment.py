from fastapi import APIRouter, Request

from suraj_dada.schemas.assessment import AssessmentCreate, AssessmentResponse, AssessmentResult

router = APIRouter()


@router.post("/", response_model=AssessmentResponse, status_code=201)
async def create_assessment(request: Request, data: AssessmentCreate):
    svc = request.app.state.context.assessment
    return await svc.create_assessment(data)


@router.post("/{assessment_id}/answer")
async def submit_answer(request: Request, assessment_id: str, data: dict):
    svc = request.app.state.context.assessment
    question_id = data.get("question_id")
    student_answer = data.get("student_answer", "")
    return await svc.submit_answer(assessment_id, str(question_id), student_answer)


@router.post("/{assessment_id}/complete", response_model=AssessmentResult)
async def complete_assessment(request: Request, assessment_id: str):
    svc = request.app.state.context.assessment
    return await svc.complete_assessment(assessment_id)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(request: Request, assessment_id: str):
    svc = request.app.state.context.assessment
    return await svc.get_assessment(assessment_id)
