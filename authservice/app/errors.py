"""Erreurs au format RFC 9457 (application/problem+json), comme ProblemDetail côté Spring."""
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str, headers: dict | None = None):
        self.status = status
        self.code = code
        self.detail = detail
        self.headers = headers


def problem(request: Request, status: int, detail: str, code: str | None = None, **extra):
    body = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
    }
    if code:
        body["code"] = code
    body.update(extra)
    return body


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return JSONResponse(
            problem(request, exc.status, exc.detail, exc.code),
            status_code=exc.status,
            media_type=PROBLEM_JSON,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = [
            {
                "field": ".".join(str(p) for p in err["loc"] if p not in ("body", "query", "path")),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            problem(request, 400, "Request is invalid", "VALIDATION_FAILED", errors=errors),
            status_code=400,
            media_type=PROBLEM_JSON,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            problem(request, exc.status_code, str(exc.detail)),
            status_code=exc.status_code,
            media_type=PROBLEM_JSON,
            headers=getattr(exc, "headers", None),
        )
