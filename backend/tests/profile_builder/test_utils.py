"""Tests for normalisation and sanitisation utilities."""

from __future__ import annotations

import pytest

from backend.modules.profile_builder.utils import (
    normalize_degree,
    normalize_email,
    normalize_location,
    normalize_phone,
    normalize_url,
    validate_email,
    validate_phone,
)


class TestNormalizeDegree:
    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("BS", "Bachelor of Science"),
            ("b.s.", "Bachelor of Science"),
            ("MBA", "Master of Business Administration"),
            ("PhD", "Doctor of Philosophy"),
            ("ph.d.", "Doctor of Philosophy"),
            ("MS", "Master of Science"),
            ("BA", "Bachelor of Arts"),
            ("MD", "Doctor of Medicine"),
        ],
    )
    def test_known_abbreviations(self, input_val, expected):
        assert normalize_degree(input_val) == expected

    def test_unknown_degree_passes_through(self):
        assert normalize_degree("Custom Degree") == "Custom Degree"

    def test_strips_whitespace(self):
        assert normalize_degree("  BS  ") == "Bachelor of Science"


class TestNormalizeLocation:
    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("sf", "San Francisco, CA"),
            ("SF", "San Francisco, CA"),
            ("nyc", "New York, NY"),
            ("la", "Los Angeles, CA"),
            ("dc", "Washington, DC"),
            ("usa", "United States"),
            ("uk", "United Kingdom"),
        ],
    )
    def test_known_aliases(self, input_val, expected):
        assert normalize_location(input_val) == expected

    def test_unknown_location_passes_through(self):
        assert normalize_location("Austin, TX") == "Austin, TX"

    def test_collapses_whitespace(self):
        assert normalize_location("  New   York  ") == "New York"


class TestNormalizeUrl:
    def test_trailing_slash_removed(self):
        assert normalize_url("https://example.com/") == "https://example.com"

    def test_lowercase_scheme_and_host(self):
        assert normalize_url("HTTPS://EXAMPLE.COM") == "https://example.com"

    def test_preserves_path(self):
        assert normalize_url("https://example.com/path/to/page/") == (
            "https://example.com/path/to/page"
        )

    def test_strips_whitespace(self):
        assert normalize_url("  https://example.com  ") == "https://example.com"


class TestNormalizeEmail:
    def test_lowercases(self):
        assert normalize_email("Jane.DOE@Example.COM") == "jane.doe@example.com"

    def test_strips_whitespace(self):
        assert normalize_email("  jane@example.com  ") == "jane@example.com"


class TestNormalizePhone:
    def test_strips_dashes(self):
        assert normalize_phone("+1-555-123-4567") == "+15551234567"

    def test_strips_parens(self):
        assert normalize_phone("+1 (555) 123-4567") == "+15551234567"

    def test_strips_dots(self):
        assert normalize_phone("+1.555.123.4567") == "+15551234567"

    def test_strips_spaces(self):
        assert normalize_phone("+1 555 123 4567") == "+15551234567"


class TestValidateEmail:
    def test_valid(self):
        assert validate_email("user@example.com") is True

    def test_invalid(self):
        assert validate_email("not-an-email") is False

    def test_case_insensitive(self):
        assert validate_email("USER@EXAMPLE.COM") is True


class TestValidatePhone:
    def test_valid_international(self):
        assert validate_phone("+15551234567") is True

    def test_valid_simple(self):
        assert validate_phone("5551234567") is True

    def test_too_short(self):
        assert validate_phone("123") is False
