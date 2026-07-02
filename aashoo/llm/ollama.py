"""Ollama LLM — streaming + function calling via OpenAI-compatible local endpoint."""

from openai import OpenAI
from aashoo.llm.openai import OpenAILLM


class OllamaLLM(OpenAILLM):

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        # Ollama's OpenAI compatible endpoint is under /v1
        base_url = f"{ollama_url.rstrip('/')}/v1"
        # API Key is not required by local Ollama, but the OpenAI client demands a non-empty string.
        super().__init__(api_key="ollama", model=model)
        self.client = OpenAI(api_key="ollama", base_url=base_url)
