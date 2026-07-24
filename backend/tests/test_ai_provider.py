"""
Tests for app/core/ai_provider.py.

The real `anthropic` package is not installed in this environment by
design -- it's a lazy import so the rest of the codebase never depends on
it being present, and CI never needs it or a real API key. These tests
inject a fake `anthropic` module into sys.modules via monkeypatch to
exercise AnthropicAIProvider's logic without any real network dependency.
"""

import sys
import types

import pytest
from pydantic import BaseModel

from app.core.ai_provider import AICallError, AnthropicAIProvider


class _DummyResponseModel(BaseModel):
    value: str


def _make_fake_anthropic_module(create_return=None, create_raises_api_error=None, create_raises_other=None):
    """Build a minimal fake `anthropic` module sufficient for AnthropicAIProvider."""

    class FakeAPIError(Exception):
        pass

    class FakeMessages:
        def create(self, **kwargs):
            if create_raises_api_error is not None:
                raise FakeAPIError(create_raises_api_error)
            if create_raises_other is not None:
                raise create_raises_other
            return create_return

    class FakeAnthropicClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = FakeMessages()

    fake_module = types.ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropicClient
    fake_module.APIError = FakeAPIError
    return fake_module


class _FakeContentBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text):
        self.content = [_FakeContentBlock(text)]


class TestAnthropicAIProviderInit:
    def test_raises_when_anthropic_not_installed(self, monkeypatch):
        monkeypatch.delitem(sys.modules, "anthropic", raising=False)
        # No monkeypatching of the import itself needed: anthropic genuinely
        # is not installed in this environment, so this exercises the real path.
        with pytest.raises(AICallError, match="not installed"):
            AnthropicAIProvider(api_key="fake-key")

    def test_raises_when_no_api_key_configured(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "anthropic", _make_fake_anthropic_module())
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(AICallError, match="API key"):
            AnthropicAIProvider(api_key=None)

    def test_succeeds_with_explicit_api_key(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "anthropic", _make_fake_anthropic_module())
        provider = AnthropicAIProvider(api_key="fake-key")
        assert provider is not None

    def test_succeeds_with_env_var_api_key(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "anthropic", _make_fake_anthropic_module())
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        provider = AnthropicAIProvider()
        assert provider is not None


class TestAnthropicAIProviderCompleteStructured:
    def test_returns_validated_model_on_success(self, monkeypatch):
        fake_module = _make_fake_anthropic_module(create_return=_FakeResponse('{"value": "ok"}'))
        monkeypatch.setitem(sys.modules, "anthropic", fake_module)
        provider = AnthropicAIProvider(api_key="fake-key")

        result = provider.complete_structured("system", "user", _DummyResponseModel)
        assert result.value == "ok"

    def test_raises_ai_call_error_on_api_error(self, monkeypatch):
        fake_module = _make_fake_anthropic_module(create_raises_api_error="boom")
        monkeypatch.setitem(sys.modules, "anthropic", fake_module)
        provider = AnthropicAIProvider(api_key="fake-key")

        with pytest.raises(AICallError, match="Anthropic API call failed"):
            provider.complete_structured("system", "user", _DummyResponseModel)

    def test_raises_ai_call_error_on_generic_network_failure(self, monkeypatch):
        fake_module = _make_fake_anthropic_module(create_raises_other=TimeoutError("timed out"))
        monkeypatch.setitem(sys.modules, "anthropic", fake_module)
        provider = AnthropicAIProvider(api_key="fake-key")

        with pytest.raises(AICallError, match="Anthropic API call failed"):
            provider.complete_structured("system", "user", _DummyResponseModel)

    def test_raises_ai_call_error_on_invalid_json(self, monkeypatch):
        fake_module = _make_fake_anthropic_module(create_return=_FakeResponse("not json"))
        monkeypatch.setitem(sys.modules, "anthropic", fake_module)
        provider = AnthropicAIProvider(api_key="fake-key")

        with pytest.raises(AICallError, match="not valid JSON"):
            provider.complete_structured("system", "user", _DummyResponseModel)

    def test_raises_ai_call_error_on_schema_mismatch(self, monkeypatch):
        fake_module = _make_fake_anthropic_module(create_return=_FakeResponse('{"wrong_field": 1}'))
        monkeypatch.setitem(sys.modules, "anthropic", fake_module)
        provider = AnthropicAIProvider(api_key="fake-key")

        with pytest.raises(AICallError, match="did not match"):
            provider.complete_structured("system", "user", _DummyResponseModel)
