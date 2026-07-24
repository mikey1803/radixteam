"""
API Layer — per Chapter 4.6.
    POST   /jobs/upload
    GET    /jobs/{id}
    DELETE /jobs/{id}
    GET    /jobs
"""
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.shared.exceptions import NotFoundErrorApp

from .service import JDAnalyticsService

router = APIRouter()
service = JDAnalyticsService()


@router.post("/upload")
async def upload_job(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    record = service.process_upload(file.filename, raw_bytes)
    return {"success": True, "data": record}


@router.get("")
async def list_jobs():
    return {"success": True, "data": service.list_jobs()}


@router.get("/{job_id}")
async def get_job(job_id: str):
    record = service.get_job(job_id)
    if not record:
        raise NotFoundErrorApp(f"Job '{job_id}' not found.")
    return {"success": True, "data": record}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    deleted = service.delete_job(job_id)
    if not deleted:
        raise NotFoundErrorApp(f"Job '{job_id}' not found.")
    return {"success": True, "data": {"id": job_id, "deleted": True}}
