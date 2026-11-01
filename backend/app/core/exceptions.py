"""Custom exceptions and centralized FastAPI exception handlers."""

import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("schemasense.exceptions")


class AppException(Exception):
    """Base application exception for domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


# Alias for domain clarity
SchemaSenseException = AppException


class CapabilityUnavailableException(AppException):
    """Raised when an inactive or future capability is accessed."""

    def __init__(
        self,
        capability: str,
        phase: str = "Phase 2",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"Capability '{capability}' is inactive in Phase 1 (scheduled for {phase}).",
            code="CAPABILITY_UNAVAILABLE",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            details={"capability": capability, "scheduled_phase": phase, **(details or {})},
        )


class ModelUnavailableException(AppException):
    """Raised when AI model is not ready, not loaded, or cannot be loaded."""

    def __init__(
        self,
        message: str = "AI Model is currently unavailable.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="MODEL_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {},
        )


class ModelInferenceException(AppException):
    """Raised when AI inference fails during generation."""

    def __init__(
        self,
        message: str = "AI model generation failed.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="MODEL_INFERENCE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {},
        )


class DatabaseNotFoundException(AppException):
    """Raised when requested database is not found."""

    def __init__(
        self,
        database_id: str,
    ) -> None:
        super().__init__(
            message=f"Database with identifier '{database_id}' was not found.",
            code="DATABASE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"database_id": database_id},
        )


class NoActiveDatabaseException(AppException):
    """Raised when no database is currently active."""

    def __init__(
        self,
        message: str = "No database is currently active. Please select or activate a database first.",
    ) -> None:
        super().__init__(
            message=message,
            code="NO_ACTIVE_DATABASE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform JSON error handlers on the FastAPI app instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        logger.warning("Application exception [%s]: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "details": {"status_code": exc.status_code},
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled server exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": {},
                }
            },
        )
