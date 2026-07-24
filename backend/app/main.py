"""
Talencia — FastAPI Application Entry Point.

Registers all module routers (via app.api.router's aggregation), global
exception handlers, and startup events. This is the single entry point
for the backend.

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.logging import get_logger, set_request_id
from app.db.base import Base
from app.db.session import engine
from app.shared.exceptions import (
    TalenciaBaseError,
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
)

settings = get_settings()
logger = get_logger(__name__)


# ─── Lifespan (startup/shutdown) ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Talencia backend started successfully")
    yield
    logger.info("Talencia backend shutting down")


# ─── Create FastAPI App ─────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Talent Intelligence Platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS Middleware ────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request ID Middleware ──────────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Assign a unique request ID to every incoming request."""
    request_id = set_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ─── Global Exception Handlers ─────────────────────────────────────────

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors → 400."""
    logger.warning(f"Validation Error | {exc.message} | errors={exc.errors}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "errors": exc.errors,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors → 404."""
    logger.warning(f"Not Found | {exc.message}")
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": exc.message,
            "errors": exc.errors,
        },
    )


@app.exception_handler(DuplicateError)
async def duplicate_error_handler(request: Request, exc: DuplicateError):
    """Handle duplicate resource errors → 409."""
    logger.warning(f"Duplicate Error | {exc.message}")
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "message": exc.message,
            "errors": exc.errors,
        },
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors → 500."""
    logger.error(f"Database Error | {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": exc.message,
            "errors": exc.errors,
        },
    )


@app.exception_handler(TalenciaBaseError)
async def talencia_base_error_handler(request: Request, exc: TalenciaBaseError):
    """Catch-all for any other shared exception type → 500."""
    logger.error(f"Application Error | {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": exc.message,
            "errors": exc.errors,
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions → 500."""
    logger.error(f"Internal Error | {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal error occurred",
            "errors": [str(exc)],
        },
    )


# ─── Register Routers ───────────────────────────────────────────────────

app.include_router(api_router)


# ─── Health Check ────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "message": "Talencia API is running",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
