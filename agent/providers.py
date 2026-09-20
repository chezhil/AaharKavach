"""Choose which model backs the Strands agent.

Groq is the default: it speaks the OpenAI wire format, supports the tool
calling the knowledge-base lookups need, and has a free tier, so the project
runs for anyone who clones it with one API key and no cloud account.

    AAHAR_MODEL_PROVIDER=groq       # default; needs GROQ_API_KEY
    AAHAR_MODEL_PROVIDER=anthropic  # needs ANTHROPIC_API_KEY + `pip install anthropic`
    AAHAR_MODEL_PROVIDER=ollama     # needs a local ollama + `pip install ollama`
    AAHAR_MODEL_PROVIDER=litellm    # anything LiteLLM supports

With no provider configured the deterministic rulebook answers instead, which
is a safe default rather than an error.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "groq"


class ProviderUnavailable(RuntimeError):
    """The chosen provider isn't installed or isn't configured."""


def provider_name() -> str:
    return (os.environ.get("AAHAR_MODEL_PROVIDER") or DEFAULT_PROVIDER).strip().lower()


def provider_chain() -> list[str]:
    """The provider to try, then any fallbacks.

    Empty by default. Set AAHAR_MODEL_FALLBACK to a comma-separated list to
    chain one — e.g. ``AAHAR_MODEL_FALLBACK=ollama`` to fail over to a local
    model when the primary is rate-limited.
    """
    primary = provider_name()
    override = os.environ.get("AAHAR_MODEL_FALLBACK")
    rest = [p.strip().lower() for p in (override or "").split(",") if p.strip()]
    return [primary] + [p for p in rest if p != primary]


def model_id() -> str:
    """The model to ask for, or "" to use the provider's own default."""
    return os.environ.get("AAHAR_MODEL_ID", "").strip()


def build_model(provider: str | None = None):
    """Return a Strands model for the configured provider.

    Raises ProviderUnavailable with an actionable message rather than letting a
    bare ImportError surface three layers up.
    """
    provider = (provider or provider_name()).strip().lower()
    configured_id = model_id()
    # A model id set for one vendor is meaningless to another.
    if provider != provider_name():
        configured_id = ""

    if provider == "bedrock":
        raise ProviderUnavailable(
            "Amazon Bedrock is no longer a supported provider — set "
            "AAHAR_MODEL_PROVIDER=groq (and GROQ_API_KEY) in your .env. "
            "Without this the deterministic rulebook would answer silently."
        )

    if provider == "groq":
        # Groq speaks the OpenAI wire format, so the OpenAI provider reaches it
        # with a different base_url. Fast, free tier, and supports the tool
        # calling the knowledge-base lookups need.
        try:
            from strands.models.openai import OpenAIModel
        except ImportError as exc:
            raise ProviderUnavailable("pip install openai") from exc
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ProviderUnavailable(
                "Set GROQ_API_KEY — put it in the repo-root .env "
                "(copy .env.example), or get one free at console.groq.com/keys."
            )
        return OpenAIModel(
            client_args={
                "api_key": api_key,
                "base_url": os.environ.get(
                    "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
                ),
                # The client's default is to retry a 429 with exponential
                # backoff, which on a rate-limited free tier spends the entire
                # 29s API Gateway budget waiting and then returns a 504. One
                # retry, then let the caller fall back to the rulebook — an
                # allergen app answering from its rulebook beats one that
                # times out.
                "max_retries": int(os.environ.get("AAHAR_MODEL_MAX_RETRIES", "1")),
                "timeout": float(os.environ.get("AAHAR_MODEL_TIMEOUT", "8")),
            },
            # Needs tool-calling support for the knowledge-base lookups.
            # Which models a Groq account can reach varies; list yours with
            # `client.models.list()` if this one 404s.
            model_id=configured_id or "openai/gpt-oss-120b",
            params={"temperature": 0},
        )

    if provider == "anthropic":
        try:
            from strands.models.anthropic import AnthropicModel
        except ImportError as exc:
            raise ProviderUnavailable("pip install anthropic") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ProviderUnavailable("Set ANTHROPIC_API_KEY to use the anthropic provider.")
        return AnthropicModel(
            model_id=configured_id or "claude-sonnet-5",
            client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
            max_tokens=2048,
        )

    if provider == "ollama":
        try:
            from strands.models.ollama import OllamaModel
        except ImportError as exc:
            raise ProviderUnavailable("pip install ollama, and run `ollama serve`") from exc
        return OllamaModel(
            host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            model_id=configured_id or "llama3.1",
        )

    if provider == "litellm":
        try:
            from strands.models.litellm import LiteLLMModel
        except ImportError as exc:
            raise ProviderUnavailable("pip install litellm") from exc
        if not configured_id:
            raise ProviderUnavailable("Set AAHAR_MODEL_ID to a LiteLLM model string.")
        return LiteLLMModel(model_id=configured_id)

    raise ProviderUnavailable(
        f"Unknown AAHAR_MODEL_PROVIDER '{provider}'. "
        "Use groq, anthropic, ollama or litellm."
    )


def is_configured() -> bool:
    """True when *any* provider in the chain could run."""
    for candidate in provider_chain():
        try:
            build_model(candidate)
            return True
        except Exception as exc:
            logger.info("Provider %s not ready: %s", candidate, exc)
    return False
