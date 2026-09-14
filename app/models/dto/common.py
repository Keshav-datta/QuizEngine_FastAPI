from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    details: Any | None = None


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
    error: ErrorResponse | None = None
