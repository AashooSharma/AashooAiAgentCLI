"""OpenAI LLM — streaming + function calling."""

import os
from typing import Iterator
from openai import OpenAI
from aashoo.llm.base import BaseLLM


class OpenAILLM(BaseLLM):

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """Full response ek saath return karo."""
        kwargs = dict(
            model=self._model,
            messages=messages,
            temperature=0.4,
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
            if "tool" in err or "function" in err or "Failed to call" in err:
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
                    raise RuntimeError(f"OpenAI retry fail: {e2}")
            raise
    
    def stream_chat(self, messages: list[dict], tools: list[dict] = None) -> Iterator[str]:
        """Token-by-token stream."""
        stream = self.client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.4,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
