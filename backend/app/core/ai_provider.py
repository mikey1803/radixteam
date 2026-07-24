"""
AI Provider Abstraction.

A minimal, provider-agnostic interface every module's AI-dependent logic
should depend on, never a concrete vendor SDK directly — this is what
lets any module (Skill Matching today; JD Analytics, Talent Check, etc.
later) swap the underlying LLM provider in one place, and what lets
AI-dependent code be fully unit-tested without any network access: tests
substitute a fake object implementing this same interface, no vendor SDK
or API key required.

AnthropicAIProvider below imports the `anthropic` SDK lazily, inside
__init__, not at module import time — importing this module never fails
in an environment without the SDK installed or without an API key
configured. Code that only depends on the AIProvider Protocol (for type
hints, or to accept an optional provider parameter) is unaffected either
way.
"""

import json
import os
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class AICallError(Exception):
    """
    Raised by any AIProvider implementation on failure — network error,
    timeout, malformed response, schema mismatch, missing configuration.
    Callers only ever need to handle this one exception type, regardless
    of which concrete provider is in use.
    """


class AIProvider(Protocol):
    """A provider capable of returning a structured, schema-validated response for a prompt."""

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
        *,
        temperature: float = 0.2,
        timeout_seconds: float = 10.0,
    ) -> ResponseModelT:
        """Call the underlying model and return a validated instance of response_model."""
        ...


class AnthropicAIProvider:
    """Concrete AIProvider backed by the Anthropic Messages API."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-5"):
        try:
            import anthropic
        except ImportError as exc:
            raise AICallError(
                "The 'anthropic' package is not installed. Add it to requirements.txt "
                "and `pip install -r requirements.txt` to use AnthropicAIProvider."
            ) from exc

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise AICallError(
                "No Anthropic API key configured (pass api_key= or set ANTHROPIC_API_KEY)."
            )

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=resolved_key)
        self._model = model

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
        *,
        temperature: float = 0.2,
        timeout_seconds: float = 10.0,
    ) -> ResponseModelT:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=timeout_seconds,
            )
        except self._anthropic.APIError as exc:
            raise AICallError(f"Anthropic API call failed: {exc}") from exc
        except Exception as exc:  # network errors, timeouts, anything else
            raise AICallError(f"Anthropic API call failed: {exc}") from exc

        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AICallError(f"AI response was not valid JSON: {exc}") from exc

        try:
            return response_model.model_validate(data)
        except ValidationError as exc:
            raise AICallError(f"AI response did not match the expected schema: {exc}") from exc
