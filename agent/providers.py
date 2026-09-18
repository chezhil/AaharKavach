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


def model_id() -> str:
    return os.environ.get("AAHAR_BEDROCK_MODEL", "").strip()


def build_model():
    """Return a Strands model for the configured provider.

    Raises ProviderUnavailable with an actionable message rather than letting a
    bare ImportError surface three layers up.
    """
    provider = provider_name()
    configured_id = model_id()

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
                "Set GROQ_API_KEY (get one free at console.groq.com/keys)."
            )
        return OpenAIModel(
            client_args={
                "api_key": api_key,
                "base_url": os.environ.get(
                    "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
                ),
            },
            # Needs tool-calling support for the knowledge-base lookups.
            model_id=configured_id or "llama-3.3-70b-versatile",
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
    """True when the agent could run — used to skip it without raising."""
    try:
        build_model()
        return True
    except Exception as exc:
        logger.info("Model provider not ready: %s", exc)
        return False
