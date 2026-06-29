from fastapi import APIRouter, Query, Request

from suraj_dada.schemas.question import (
    AppQuestionCreate,
    AppQuestionResponse,
    MetadataFilterResult,
    QuestionFilter,
    TestQuestionCreate,
    TestQuestionResponse,
)

router = APIRouter()


@router.post("/app", response_model=AppQuestionResponse, status_code=201)
async def create_app_question(request: Request, data: AppQuestionCreate):
    svc = request.app.state.context.app_questions
    return await svc.create_question(data)


@router.post("/app/bulk", response_model=list[AppQuestionResponse], status_code=201)
async def bulk_create_app_questions(request: Request, data: list[AppQuestionCreate]):
    svc = request.app.state.context.app_questions
    return await svc.bulk_create(data)


@router.get("/app", response_model=list[AppQuestionResponse])
async def list_app_questions(
    request: Request,
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    subtopic: str | None = Query(None),
    difficulty_min: int | None = Query(None, ge=1, le=5),
    difficulty_max: int | None = Query(None, ge=1, le=5),
    question_type: str | None = Query(None),
):
    filters = QuestionFilter(
        subject=subject,
        topic=topic,
        subtopic=subtopic,
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        question_type=question_type,
    )
    svc = request.app.state.context.app_questions
    return await svc.search_by_metadata(filters)


@router.get("/app/{question_id}", response_model=AppQuestionResponse)
async def get_app_question(request: Request, question_id: int):
    svc = request.app.state.context.app_questions
    return await svc.get_question(str(question_id))


@router.post("/test", response_model=TestQuestionResponse, status_code=201)
async def create_test_question(request: Request, data: TestQuestionCreate):
    svc = request.app.state.context.test_questions
    return await svc.create_question(data)


@router.post("/test/bulk", response_model=list[TestQuestionResponse], status_code=201)
async def bulk_create_test_questions(request: Request, data: list[TestQuestionCreate]):
    svc = request.app.state.context.test_questions
    return await svc.bulk_create(data)


@router.get("/test", response_model=list[TestQuestionResponse])
async def list_test_questions(
    request: Request,
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    subtopic: str | None = Query(None),
    difficulty_min: int | None = Query(None, ge=1, le=5),
    difficulty_max: int | None = Query(None, ge=1, le=5),
    question_type: str | None = Query(None),
):
    filters = QuestionFilter(
        subject=subject,
        topic=topic,
        subtopic=subtopic,
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        question_type=question_type,
    )
    svc = request.app.state.context.test_questions
    return await svc.search_by_metadata(filters)


@router.get("/test/{question_id}", response_model=TestQuestionResponse)
async def get_test_question(request: Request, question_id: int):
    svc = request.app.state.context.test_questions
    return await svc.get_question(str(question_id))


@router.post("/search/metadata", response_model=MetadataFilterResult)
async def search_by_metadata(request: Request, filters: QuestionFilter):
    svc = request.app.state.context.metadata_filter
    return await svc.filter_by_criteria(filters)
