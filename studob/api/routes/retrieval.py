from fastapi import APIRouter, Request

from studob.schemas.retrieval import ContextPackage, RetrievalRequest

router = APIRouter()


@router.post("/retrieve", response_model=ContextPackage)
async def retrieve_context(request: Request, data: RetrievalRequest):
    svc = request.app.state.context.retrieval
    return await svc.retrieve(data)


@router.get("/health")
async def retrieval_health_check(request: Request):
    svc = request.app.state.context.retrieval
    return await svc.health_check()
