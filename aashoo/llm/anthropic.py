"""Anthropic LLM — streaming + function calling."""

import os
import json
from typing import Iterator
from anthropic import Anthropic
from aashoo.llm.base import BaseLLM


class DummyFunc:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class DummyToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.type = "function"
        self.function = DummyFunc(name, arguments)


def convert_to_anthropic(messages: list[dict]) -> tuple[str, list[dict]]:
    """Converts OpenAI format messages to Anthropic format."""
    system_prompt = ""
    anthropic_msgs = []
    
    # 1. Extract system prompt
    for m in messages:
        if m["role"] == "system":
            system_prompt += m["content"] + "\n"
            
    # 2. Build message blocks
    for m in messages:
        role = m["role"]
        if role == "system":
            continue
            
        if role == "user":
            anthropic_msgs.append({
                "role": "user",
                "content": m["content"]
            })
        elif role == "assistant":
            content = []
            if m.get("content"):
                content.append({
                    "type": "text",
                    "text": m["content"]
                })
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    tc_id = getattr(tc, "id", None) or tc.get("id")
                    tc_func = getattr(tc, "function", None) or tc.get("function")
                    tc_name = getattr(tc_func, "name", None) or tc_func.get("name")
                    tc_args_str = getattr(tc_func, "arguments", None) or tc_func.get("arguments")
                    
                    try:
                        tc_args = json.loads(tc_args_str) if isinstance(tc_args_str, str) else tc_args_str
                    except:
                        tc_args = {}
                    
                    content.append({
                        "type": "tool_use",
                        "id": tc_id,
                        "name": tc_name,
                        "input": tc_args
                    })
            anthropic_msgs.append({
                "role": "assistant",
                "content": content if content else ""
            })
        elif role == "tool":
            tc_id = m.get("tool_call_id")
            result_content = m.get("content", "")
            
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tc_id,
                "content": result_content
            }
            
            if anthropic_msgs and anthropic_msgs[-1]["role"] == "user":
                last_msg = anthropic_msgs[-1]
                if isinstance(last_msg["content"], list):
                    last_msg["content"].append(tool_result_block)
                else:
                    last_msg["content"] = [
                        {"type": "text", "text": last_msg["content"]},
                        tool_result_block
                    ]
            else:
                anthropic_msgs.append({
                    "role": "user",
                    "content": [tool_result_block]
                })

    # 3. Merge consecutive messages of the same role
    merged_msgs = []
    for msg in anthropic_msgs:
        if not merged_msgs:
            merged_msgs.append(msg)
            continue
        
        last = merged_msgs[-1]
        if last["role"] == msg["role"]:
            last_content = last["content"]
            if isinstance(last_content, str):
                last_content = [{"type": "text", "text": last_content}] if last_content else []
            
            msg_content = msg["content"]
            if isinstance(msg_content, str):
                msg_content = [{"type": "text", "text": msg_content}] if msg_content else []
                
            last["content"] = last_content + msg_content
        else:
            merged_msgs.append(msg)

    return system_prompt.strip(), merged_msgs


class AnthropicLLM(BaseLLM):

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-latest"):
        self.client = Anthropic(api_key=api_key)
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool schema to Anthropic format."""
        if not tools:
            return []
        anthropic_tools = []
        for t in tools:
            if t["type"] == "function":
                f = t["function"]
                anthropic_tools.append({
                    "name": f["name"],
                    "description": f.get("description", ""),
                    "input_schema": f.get("parameters", {"type": "object", "properties": {}})
                })
        return anthropic_tools

    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """Full response ek saath return karo."""
        system_prompt, anthropic_messages = convert_to_anthropic(messages)
        anthropic_tools = self._convert_tools(tools)

        kwargs = dict(
            model=self._model,
            messages=anthropic_messages,
            max_tokens=4000,
            temperature=0.4,
        )
        if system_prompt:
            kwargs["system"] = system_prompt
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        try:
            response = self.client.messages.create(**kwargs)
            
            content_text = ""
            tool_calls = []
            
            for content_block in response.content:
                if content_block.type == "text":
                    content_text += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append(
                        DummyToolCall(
                            id=content_block.id,
                            name=content_block.name,
                            arguments=json.dumps(content_block.input)
                        )
                    )
            
            return {
                "content": content_text,
                "tool_calls": tool_calls,
                "raw": response,
            }
        except Exception as e:
            err = str(e)
            if "tool" in err or "function" in err or "tool_use" in err:
                kwargs.pop("tools", None)
                kwargs["temperature"] = 0.2
                try:
                    response = self.client.messages.create(**kwargs)
                    content_text = ""
                    for content_block in response.content:
                        if content_block.type == "text":
                            content_text += content_block.text
                    return {
                        "content": content_text,
                        "tool_calls": [],
                        "raw": response,
                    }
                except Exception as e2:
                    raise RuntimeError(f"Anthropic retry fail: {e2}")
            raise
    
    def stream_chat(self, messages: list[dict], tools: list[dict] = None) -> Iterator[str]:
        """Token-by-token stream (no tools)."""
        system_prompt, anthropic_messages = convert_to_anthropic(messages)
        
        kwargs = dict(
            model=self._model,
            messages=anthropic_messages,
            max_tokens=4000,
            temperature=0.4,
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
