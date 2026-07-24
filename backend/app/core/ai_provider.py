"""
AI Provider abstraction layer.

Supports pluggable AI backends (Gemini, OpenAI, etc.)
configured via the AI_PROVIDER environment variable.
Falls back to MockProvider when no API key is configured.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate a text completion from the given prompt."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        *,
        response_schema: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Any:
        """Generate a structured (JSON) response. Returns dict or list."""
        ...

    def _extract_json(self, text: str) -> Any:
        """Extract JSON from AI response text (handles markdown code blocks)."""
        # Try direct parse first
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try extracting from markdown code block
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not parse JSON from AI response: {text[:200]}")


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            self._available = True
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.warning(f"Gemini provider init failed: {e}. Using mock.")
            self._available = False

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self._available:
            return MockProvider().generate_sync(prompt)
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        response = self.model.generate_content(
            full_prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return response.text

    async def generate_structured(
        self,
        prompt: str,
        *,
        response_schema: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Any:
        text = await self.generate(
            prompt, system_instruction=system_instruction, temperature=temperature
        )
        return self._extract_json(text)


class MockProvider(BaseAIProvider):
    """Mock AI provider for development/demo without API keys."""

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        return self.generate_sync(prompt)

    def generate_sync(self, prompt: str) -> str:
        """Synchronous mock generation for fallback."""
        prompt_lower = prompt.lower()
        if "interview" in prompt_lower or "question" in prompt_lower:
            return json.dumps([
                {"question": "Can you walk me through a complex API you built with FastAPI?", "focus_area": "Backend Development"},
                {"question": "How would you containerize a Python application using Docker?", "focus_area": "Docker"},
                {"question": "Describe your experience with cloud deployment (AWS/GCP).", "focus_area": "Cloud/DevOps"},
                {"question": "How do you handle database migrations in production?", "focus_area": "Database Management"},
                {"question": "Tell me about a time you optimized a slow SQL query.", "focus_area": "SQL Performance"},
            ])
        elif "resume" in prompt_lower and ("extract" in prompt_lower or "parser" in prompt_lower or "parse" in prompt_lower):
            return json.dumps({
                "name": "Demo Candidate",
                "email": "demo@example.com",
                "phone": "+1-555-0100",
                "skills": ["Python", "JavaScript", "SQL", "FastAPI", "React"],
                "experience_years": 3.0,
                "education": [{"degree": "B.Tech Computer Science", "institution": "Demo University", "year": "2021"}],
            })
        elif "evaluate" in prompt_lower or "talent" in prompt_lower:
            return json.dumps({
                "overall_score": 72.0,
                "skill_match_score": 78.0,
                "experience_score": 65.0,
                "matched_skills": ["Python", "SQL", "FastAPI"],
                "skill_gaps": ["Docker", "Kubernetes", "AWS"],
                "reasoning": "Candidate shows strong Python and backend skills. Missing cloud/DevOps experience. Recommended for further interview to assess system design depth.",
            })
        return json.dumps({"message": "Mock AI response"})

    async def generate_structured(
        self,
        prompt: str,
        *,
        response_schema: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        text = await self.generate(prompt)
        return self._extract_json(text)


# ── Factory ──────────────────────────────────────────────────────────────────
_PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": MockProvider,  # OpenAI not yet implemented, use mock
    "mock": MockProvider,
}


def get_ai_provider() -> BaseAIProvider:
    """Return the configured AI provider instance. Falls back to Mock if no key."""
    settings = get_settings()
    provider_name = settings.AI_PROVIDER.lower()

    # Fall back to mock if no API key configured
    if provider_name == "gemini" and not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY set. Using MockProvider for demo mode.")
        return MockProvider()

    if provider_name not in _PROVIDERS:
        logger.warning(f"Unknown provider '{provider_name}'. Falling back to MockProvider.")
        return MockProvider()

    return _PROVIDERS[provider_name]()
