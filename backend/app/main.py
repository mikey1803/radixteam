"""
FastAPI app entrypoint.

Layered architecture per Chapter 2.1:
    React Frontend -> FastAPI (this file + api/) -> Service -> Repository -> Storage
"""
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.shared.exceptions import AppError

setup_logging()
logger = get_logger("radix.main")

app = FastAPI(title="RADIX Talent Match API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.time()
    request.state.request_id = request_id

    response = await call_next(request)

    latency_ms = round((time.time() - start) * 1000, 1)
    logger.info(
        f"{request.method} {request.url.path} | status={response.status_code} | "
        f"latency_ms={latency_ms}",
        extra={"request_id": request_id},
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error(f"{exc.category}: {exc.message}",
                 extra={"request_id": getattr(request.state, "request_id", "-")})
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())


@app.get("/health")
def health():
    return {"success": True, "data": {"status": "ok", "ai_mode": settings.ai_provider_mode}}


app.include_router(api_router)
