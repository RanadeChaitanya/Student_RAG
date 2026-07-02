from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from studob.api.dependencies import AppContext
from studob.api.middleware import AuthMiddleware, ErrorHandlingMiddleware, LoggingMiddleware
from studob.api.routes import (
    analytics,
    assessment,
    auth,
    graph,
    practice,
    questions,
    reports,
    retrieval,
    sessions,
    students,
)
from studob.config.loader import get_config
from studob.logging_setup import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_config()
    setup_logging(settings.app.log_level)
    logger = get_logger("api")
    logger.info(
        "Starting Studob API server", extra={"context": {"version": settings.app.version}}
    )

    context = AppContext()
    await context.initialize(settings)
    app.state.context = context
    app.state.settings = settings

    from pathlib import Path as _Path
    missing = []
    if not _Path(settings.database.graph.data_path).exists():
        missing.append(f"concept graph ({settings.database.graph.data_path})")
    if not _Path(settings.database.vector.index_path).exists():
        missing.append(f"FAISS index ({settings.database.vector.index_path})")
    if missing:
        logger.warning("Missing data files on startup", extra={"files": missing})

    yield

    logger.info("Shutting down Studob API server")
    if context.db_engine:
        await context.db_engine.close_db()


app = FastAPI(
    title="Studob API",
    description="AI-powered adaptive tutoring platform for JEE students",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(AuthMiddleware)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(retrieval.router, prefix="/api/v1/retrieval", tags=["Retrieval"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Concept Graph"])
app.include_router(practice.router, prefix="/api/v1/practice", tags=["Practice"])
app.include_router(assessment.router, prefix="/api/v1/assessment", tags=["Assessment"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])


@app.get("/")
async def index():
    return HTMLResponse(Path("studob/api/static/index.html").read_text(encoding="utf-8"))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
