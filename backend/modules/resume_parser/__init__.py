"""Resume Parser module — extracts structured data from PDF and DOCX resumes."""

from backend.modules.resume_parser.api import router as resume_router
from backend.modules.resume_parser.service import ResumeParserService

__all__ = ["resume_router", "ResumeParserService"]
