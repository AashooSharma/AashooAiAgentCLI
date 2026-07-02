"""Base LLM interface — sab providers isko implement karenge."""

from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLM(ABC):

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """Single response return karo (non-streaming)."""
        pass

    @abstractmethod
    def stream_chat(self, messages: list[dict], tools: list[dict] = None) -> Iterator[str]:
        """Token-by-token stream karo."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass