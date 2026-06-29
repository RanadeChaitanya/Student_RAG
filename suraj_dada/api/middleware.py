import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from suraj_dada.exceptions import DatabaseError, NotFoundError, SurajDadaError, ValidationError
from suraj_dada.logging_setup import get_logger

logger = get_logger("api.middleware")


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
        except ValidationError as e:
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
        except SurajDadaError as e:
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
