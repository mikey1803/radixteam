"""
Text Extraction + Cleaning — per Chapter 4.8 / 4.9.

Never call AI directly on binary files — always extract plain text first.
Preferred: PyMuPDF for PDF, python-docx for DOCX. Falls back to pdfplumber
if PyMuPDF fails on a given PDF.
"""
from __future__ import annotations

import io
import re

from app.shared.exceptions import FileErrorApp


def extract_text(raw_bytes: bytes, extension: str) -> str:
    if extension == ".pdf":
        return _extract_pdf_text(raw_bytes)
    if extension == ".docx":
        return _extract_docx_text(raw_bytes)
    raise FileErrorApp(f"No extractor available for '{extension}'.")


def _extract_pdf_text(raw_bytes: bytes) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        if doc.is_encrypted:
            raise FileErrorApp(
                "Password-protected PDFs are not supported.",
                errors=[{"field": "file", "reason": "password_protected"}],
            )
        text = "\n".join(page.get_text() for page in doc)
        if text.strip():
            return text
    except FileErrorApp:
        raise
    except Exception:
        pass  # fall through to pdfplumber

    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        raise FileErrorApp(
            "Could not extract text from this PDF — it may be corrupted or scanned.",
            errors=[{"field": "file", "reason": "corrupted_pdf", "detail": str(e)}],
        ) from e


def _extract_docx_text(raw_bytes: bytes) -> str:
    try:
        import docx
        document = docx.Document(io.BytesIO(raw_bytes))
        return "\n".join(p.text for p in document.paragraphs)
    except Exception as e:
        raise FileErrorApp(
            "Could not extract text from this DOCX — it may be corrupted.",
            errors=[{"field": "file", "reason": "corrupted_docx", "detail": str(e)}],
        ) from e


def clean_text(raw_text: str) -> str:
    """Remove empty lines, extra whitespace, page-number-only lines, normalize unicode."""
    lines = raw_text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r"page\s*\d+(\s*of\s*\d+)?", stripped, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"\d+", stripped):
            continue
        stripped = re.sub(r"[ \t]+", " ", stripped)
        stripped = stripped.replace("\u2022", "-").replace("\u00a0", " ")
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)
