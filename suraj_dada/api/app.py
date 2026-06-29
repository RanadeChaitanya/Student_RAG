from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from suraj_dada.api.dependencies import AppContext
from suraj_dada.api.middleware import ErrorHandlingMiddleware, LoggingMiddleware
from suraj_dada.api.routes import (
    analytics,
    assessment,
    diagnosis,
    practice,
    questions,
    retrieval,
    sessions,
    students,
)
from suraj_dada.config.loader import get_config
from suraj_dada.logging_setup import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_config()
    setup_logging(settings.app.log_level)
    logger = get_logger("api")
    logger.info(
        "Starting Suraj Dada API server", extra={"context": {"version": settings.app.version}}
    )

    context = AppContext()
    await context.initialize(settings)
    app.state.context = context

    yield

    logger.info("Shutting down Suraj Dada API server")
    if context.db_engine:
        await context.db_engine.close_db()


app = FastAPI(
    title="Suraj Dada API",
    description="AI-powered adaptive tutoring platform for JEE students",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["Diagnosis"])
app.include_router(retrieval.router, prefix="/api/v1/retrieval", tags=["Retrieval"])
app.include_router(practice.router, prefix="/api/v1/practice", tags=["Practice"])
app.include_router(assessment.router, prefix="/api/v1/assessment", tags=["Assessment"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/")
async def index():
    return HTMLResponse(Path("suraj_dada/api/static/index.html").read_text(encoding="utf-8"))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
