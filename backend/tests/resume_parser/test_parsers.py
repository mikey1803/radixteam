"""Tests for low-level text extraction (parsers)."""

from __future__ import annotations

import io

import pytest
from docx import Document

from backend.modules.resume_parser.parsers import (
    extract_text,
    validate_file,
)


class TestExtractTextPDF:
    def test_extracts_text_from_valid_pdf(self):
        """Create a valid PDF with pdfplumber-compatible content."""
        import pdfplumber

        # Build a simple PDF that pdfplumber can read
        # Use the pdfplumber test helper by writing via reportlab-like bytes
        # Instead, just create a PDF with known content using fpdf if available
        # or use a minimal valid PDF
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(text="Jane Doe")
            pdf.output("/tmp/test_resume.pdf")
            with open("/tmp/test_resume.pdf", "rb") as f:
                content = f.read()
            text = extract_text(content, "test.pdf")
            assert "Jane Doe" in text
        except ImportError:
            # fpdf not installed — verify the function handles gracefully
            pytest.skip("fpdf not installed; PDF creation not available")

    def test_empty_file_raises(self):
        with pytest.raises(ValueError, match="empty"):
            extract_text(b"", "test.pdf")

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            extract_text(b"some data", "test.txt")

    def test_file_too_large_raises(self):
        large = b"x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(ValueError, match="exceeds"):
            extract_text(large, "test.pdf")


class TestExtractTextDOCX:
    def test_extracts_text_from_valid_docx(self, sample_docx_bytes):
        text = extract_text(sample_docx_bytes, "resume.docx")
        assert "Jane Doe" in text
        assert "jane@example.com" in text
        assert "Acme Corp" in text
        assert "Python" in text

    def test_empty_docx_raises(self):
        doc = Document()
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        with pytest.raises(ValueError, match="No text content"):
            extract_text(buf.read(), "empty.docx")


class TestValidateFile:
    def test_valid_pdf(self):
        ext = validate_file("resume.pdf", 1024)
        assert ext == ".pdf"

    def test_valid_docx(self):
        ext = validate_file("resume.docx", 2048)
        assert ext == ".docx"

    def test_unsupported_type(self):
        with pytest.raises(ValueError, match="Unsupported"):
            validate_file("resume.txt", 1024)

    def test_too_large(self):
        with pytest.raises(ValueError, match="too large"):
            validate_file("resume.pdf", 10 * 1024 * 1024 + 1)
