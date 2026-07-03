"""LLM clients initialization."""

from aashoo.llm.base import BaseLLM
from aashoo.llm.groq import GroqLLM
from aashoo.llm.google import GoogleLLM
from aashoo.llm.openai import OpenAILLM
from aashoo.llm.anthropic import AnthropicLLM
from aashoo.llm.ollama import OllamaLLM


def get_llm_client(config: dict) -> BaseLLM:
    """Instantiate the configured LLM provider and active key."""
    provider = config.get("llm_provider", "groq")

    # Per-provider model — pehle {provider}_model check karo, phir old 'model', phir default
    PROVIDER_DEFAULTS = {
        "groq": "llama-3.3-70b-versatile",
        "google": "gemini-2.5-flash",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-latest",
        "ollama": "llama3",
    }
    model = (
        config.get(f"{provider}_model")
        or config.get("model")
        or PROVIDER_DEFAULTS.get(provider, "llama-3.3-70b-versatile")
    )

    if provider == "groq":
        keys = config.get("groq_api_keys", [])
        if not keys and config.get("groq_api_key"):
            keys = [config["groq_api_key"]]
        idx = config.get("active_groq_key_idx", 0)
        api_key = keys[idx] if idx < len(keys) else (keys[0] if keys else "")
        return GroqLLM(api_key=api_key, model=model)

    elif provider == "google":
        keys = config.get("google_api_keys", [])
        if not keys and config.get("google_api_key"):
            keys = [config["google_api_key"]]
        idx = config.get("active_google_key_idx", 0)
        api_key = keys[idx] if idx < len(keys) else (keys[0] if keys else "")
        return GoogleLLM(api_key=api_key, model=model)

    elif provider == "openai":
        keys = config.get("openai_api_keys", [])
        if not keys and config.get("openai_api_key"):
            keys = [config["openai_api_key"]]
        idx = config.get("active_openai_key_idx", 0)
        api_key = keys[idx] if idx < len(keys) else (keys[0] if keys else "")
        return OpenAILLM(api_key=api_key, model=model)

    elif provider == "anthropic":
        keys = config.get("anthropic_api_keys", [])
        if not keys and config.get("anthropic_api_key"):
            keys = [config["anthropic_api_key"]]
        idx = config.get("active_anthropic_key_idx", 0)
        api_key = keys[idx] if idx < len(keys) else (keys[0] if keys else "")
        return AnthropicLLM(api_key=api_key, model=model)

    elif provider == "ollama":
        url = config.get("ollama_url", "http://localhost:11434")
        return OllamaLLM(ollama_url=url, model=model)

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

