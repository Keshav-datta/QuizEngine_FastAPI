from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import AppException


STATUS_CODES = {
    "USER_ALREADY_EXISTS": 409,
    "INVALID_CREDENTIALS": 401,
    "USER_NOT_FOUND": 404,
    "QUIZ_NOT_FOUND": 404,
    "QUIZ_NOT_OWNED": 403,
    "QUIZ_NOT_PUBLISHED": 409,
    "QUIZ_NOT_DRAFT": 409,
    "QUIZ_EMPTY": 409,
    "QUESTION_NOT_FOUND": 404,
    "INVALID_QUESTION": 404,
    "INVALID_QUESTION_DATA": 400,
    "MCQ_OPTIONS_REQUIRED": 400,
    "MCQ_CORRECT_OPTION_REQUIRED": 400,
    "MCQ_INVALID_ANSWER": 400,
    "SUBJECTIVE_ANSWER_REQUIRED": 400,
    "SUBJECTIVE_OPTIONS_NOT_ALLOWED": 400,
    "QUESTION_NOT_OWNED": 403,
    "ATTEMPT_NOT_FOUND": 404,
    "ATTEMPT_NOT_OWNED": 403,
    "ATTEMPT_ALREADY_ACTIVE": 409,
    "ATTEMPT_NOT_ACTIVE": 409,
    "ATTEMPT_EXPIRED": 409,
    "INVALID_OPTION": 400,
    "ANSWER_ALREADY_EXISTS": 409,
}


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=STATUS_CODES.get(exc.code, 400),
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error": {"code": exc.code, "details": None},
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": str(exc.detail),
                "data": None,
                "error": {"code": "HTTP_ERROR", "details": None},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(x) for x in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Request validation failed",
                "data": None,
                "error": {"code": "VALIDATION_ERROR", "details": details},
            },
        )
