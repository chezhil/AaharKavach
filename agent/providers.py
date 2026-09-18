"""Choose which model backs the Strands agent.

The submission targets Bedrock, but Bedrock needs an AWS account, and waiting
for one leaves the single riskiest question unanswered: does the agent actually
produce valid structured output for this schema and prompt?

Strands can drive several providers behind the same Agent API, so that question
can be answered today against Ollama (free, local) or the Anthropic API, and the
switch to Bedrock is then one environment variable — not a rewrite.

    AAHAR_MODEL_PROVIDER=bedrock    # default; needs AWS credentials
    AAHAR_MODEL_PROVIDER=groq       # needs GROQ_API_KEY + `pip install openai`
    AAHAR_MODEL_PROVIDER=anthropic  # needs ANTHROPIC_API_KEY + `pip install anthropic`
    AAHAR_MODEL_PROVIDER=ollama     # needs a local ollama + `pip install ollama`
    AAHAR_MODEL_PROVIDER=litellm    # anything LiteLLM supports
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "bedrock"


class ProviderUnavailable(RuntimeError):
    """The chosen provider isn't installed or isn't configured."""


def provider_name() -> str:
    return (os.environ.get("AAHAR_MODEL_PROVIDER") or DEFAULT_PROVIDER).strip().lower()


def provider_chain() -> list[str]:
    """The provider to try, then its fallbacks.

    Bedrock can be held by account verification or throttled; Groq is a
    different vendor entirely, so one covers the other. Set
    AAHAR_MODEL_FALLBACK to change it, or to "" to disable chaining.
    """
    primary = provider_name()
    override = os.environ.get("AAHAR_MODEL_FALLBACK")
    if override is not None:
        rest = [p.strip().lower() for p in override.split(",") if p.strip()]
    elif primary == "bedrock":
        rest = ["groq"]
    else:
        rest = []
    return [primary] + [p for p in rest if p != primary]


def model_id() -> str:
    return os.environ.get("AAHAR_BEDROCK_MODEL", "").strip()


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
        from strands.models.bedrock import BedrockModel

        if not configured_id:
            raise ProviderUnavailable(
                "Set AAHAR_BEDROCK_MODEL to a model enabled in your Bedrock account "
                "(list them with `aws bedrock list-inference-profiles`)."
            )
        return BedrockModel(
            model_id=configured_id,
            region_name=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
        )

    if provider == "groq":
        # Groq speaks the OpenAI wire format, so the OpenAI provider reaches it
        # with a different base_url. Fast and has a free tier, which makes it a
        # practical stand-in for Bedrock while an AWS account is pending.
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
            raise ProviderUnavailable("Set AAHAR_BEDROCK_MODEL to a LiteLLM model string.")
        return LiteLLMModel(model_id=configured_id)

    raise ProviderUnavailable(
        f"Unknown AAHAR_MODEL_PROVIDER '{provider}'. "
        "Use bedrock, groq, anthropic, ollama or litellm."
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
