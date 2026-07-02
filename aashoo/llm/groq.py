"""Groq LLM — streaming + function calling."""

import os
from typing import Iterator
from groq import Groq
from aashoo.llm.base import BaseLLM


class GroqLLM(BaseLLM):

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    # def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
    #     """Full response ek saath return karo (tool calling ke liye)."""
    #     kwargs = dict(
    #         model=self._model,
    #         messages=messages,
    #         temperature=0.4,
    #         max_completion_tokens=4096,
    #     )
    #     if tools:
    #         kwargs["tools"] = tools
    #         kwargs["tool_choice"] = "auto"

    #     response = self.client.chat.completions.create(**kwargs)
    #     choice = response.choices[0].message

    #     return {
    #         "content": choice.content or "",
    #         "tool_calls": choice.tool_calls or [],
    #         "raw": choice,
    #     }

    # groq.py mein chat() function replace karo:
    
    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """Full response ek saath return karo."""
        kwargs = dict(
            model=self._model,
            messages=messages,
            temperature=0.4,
            max_completion_tokens=4096,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0].message
            return {
                "content": choice.content or "",
                "tool_calls": choice.tool_calls or [],
                "raw": choice,
            }
        except Exception as e:
            err = str(e)
            # tool_use_failed → retry WITHOUT tools (text-only response lelo)
            if "tool_use_failed" in err or "Failed to call a function" in err:
                kwargs.pop("tools", None)
                kwargs.pop("tool_choice", None)
                kwargs["temperature"] = 0.2
                try:
                    response = self.client.chat.completions.create(**kwargs)
                    choice = response.choices[0].message
                    return {
                        "content": choice.content or "",
                        "tool_calls": [],
                        "raw": choice,
                    }
                except Exception as e2:
                    raise RuntimeError(f"Groq retry bhi fail: {e2}")
            raise
    
    def stream_chat(self, messages: list[dict], tools: list[dict] = None) -> Iterator[str]:
        """Token-by-token stream — sirf text (no tool calling)."""
        stream = self.client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.4,
            max_completion_tokens=4096,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content