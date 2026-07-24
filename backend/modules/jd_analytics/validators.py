"""
Upload validation — per Chapter 4.7.
Accept only PDF / DOCX, reject everything else, enforce size limit,
reject corrupted / password-protected files.
"""
from __future__ import annotations

from app.shared.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from app.shared.exceptions import FileErrorApp, ValidationErrorApp


def validate_extension(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationErrorApp(
            f"Unsupported file type '{ext}'. Only PDF and DOCX are accepted.",
            errors=[{"field": "file", "reason": "unsupported_extension"}],
        )
    return ext


def validate_size(size_bytes: int) -> None:
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileErrorApp(
            f"File exceeds the {MAX_UPLOAD_SIZE_MB}MB limit.",
            errors=[{"field": "file", "reason": "file_too_large"}],
        )
    if size_bytes == 0:
        raise FileErrorApp(
            "Uploaded file is empty.",
            errors=[{"field": "file", "reason": "empty_file"}],
        )


def validate_not_corrupted_pdf(raw_bytes: bytes) -> None:
    if not raw_bytes.startswith(b"%PDF-"):
        raise FileErrorApp(
            "File does not look like a valid PDF.",
            errors=[{"field": "file", "reason": "corrupted_pdf"}],
        )
