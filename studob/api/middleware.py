import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from studob.exceptions import (
    DatabaseError,
    DomainValidationError,
    NotFoundError,
    StudobError,
)
from studob.logging_setup import get_logger

logger = get_logger("api.middleware")

SKIP_AUTH_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = getattr(request.app.state, "settings", None)
        api_key_setting = settings.app.api_key if settings else ""

        if not api_key_setting:
            return await call_next(request)

        path = request.url.path
        if path in SKIP_AUTH_PATHS or path.startswith("/docs") or path.startswith("/openapi.json"):
            return await call_next(request)

        request_api_key = request.headers.get("X-API-Key", "")
        if request_api_key != api_key_setting:
            logger.warning("Unauthorized request", extra={"path": path})
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key", "code": "UNAUTHORIZED"},
            )

        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "HTTP Request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except NotFoundError as e:
            logger.warning("Not found", extra={"path": request.url.path, "detail": e.message})
            return JSONResponse(
                status_code=404,
                content={
                    "detail": e.message,
                    "code": e.code,
                    "resource_type": e.details.get("resource_type"),
                    "resource_id": e.details.get("resource_id"),
                },
            )
        except DomainValidationError as e:
            logger.warning(
                "Validation error", extra={"path": request.url.path, "detail": e.message}
            )
            return JSONResponse(
                status_code=422,
                content={"detail": e.message, "code": e.code, "details": e.details},
            )
        except DatabaseError as e:
            logger.error("Database error", extra={"path": request.url.path, "detail": e.message})
            return JSONResponse(
                status_code=503,
                content={"detail": e.message, "code": e.code},
            )
        except StudobError as e:
            logger.error(
                "Application error",
                extra={"path": request.url.path, "code": e.code, "detail": e.message},
            )
            return JSONResponse(
                status_code=400,
                content={"detail": e.message, "code": e.code, "details": e.details},
            )
        except Exception:
            logger.exception("Unhandled exception", extra={"path": request.url.path})
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred", "code": "INTERNAL_ERROR"},
            )
