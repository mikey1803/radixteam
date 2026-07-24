"""Resume Parser API — STUB. Mirrors JD Analytics' endpoint shape."""
from fastapi import APIRouter, File, UploadFile

from app.shared.exceptions import NotFoundErrorApp
from .service import ResumeParserService

router = APIRouter()
service = ResumeParserService()


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    record = service.process_upload(file.filename, raw_bytes)
    return {"success": True, "data": record}


@router.get("")
async def list_resumes():
    return {"success": True, "data": service.list_resumes()}


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    record = service.get_resume(resume_id)
    if not record:
        raise NotFoundErrorApp(f"Resume '{resume_id}' not found.")
    return {"success": True, "data": record}
