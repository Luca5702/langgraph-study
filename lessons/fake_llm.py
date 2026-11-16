"""
一个"假的"聊天模型，用于在没有 API Key 的情况下学习 LangGraph。

* 它实现了 LangChain 的 BaseChatModel 接口，所以能被 LangGraph 的
  messages 流式模式捕获 token、能 bind_tools、能产生 tool_calls。
* 规则：
    - 最后一条是 ToolMessage   -> 根据工具结果给出最终回答
    - 用户提到 "天气" + 城市     -> 调用 get_weather
    - 用户消息里有算式 (如 12*7) -> 调用 calculator
    - 否则                       -> 普通回复

想换成真模型？设置环境变量后调用 get_model() 即可，例如：
    pip install langchain langchain-openai   (或 langchain-google-genai / langchain-anthropic)
    export LG_MODEL="openai:gpt-4.1-mini"     (或 "google_genai:gemini-2.5-flash")
"""
from __future__ import annotations

import os
import re
import uuid
from typing import Any, Iterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

CITIES = ["北京", "上海", "深圳", "旧金山", "东京"]
MATH = re.compile(r"(\d+(?:\.\d+)?\s*[-+*/]\s*\d+(?:\.\d+)?(?:\s*[-+*/]\s*\d+(?:\.\d+)?)*)")


class FakeToolModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "fake-tool-model"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "FakeToolModel":
        return self  # 规则已写死，忽略工具 schema

    # ---- 决策逻辑 ----
    def _decide(self, messages: list[BaseMessage]) -> AIMessage:
        last = messages[-1]
        if isinstance(last, ToolMessage):
            return AIMessage(content=f"根据工具「{last.name}」的结果：{last.content}。还有什么可以帮你？")
        text = str(last.content)
        if "天气" in text:
            city = next((c for c in CITIES if c in text), "北京")
            return AIMessage(content="", tool_calls=[{
                "name": "get_weather", "args": {"city": city}, "id": f"call_{uuid.uuid4().hex[:8]}"}])
        m = MATH.search(text)
        if m:
            return AIMessage(content="", tool_calls=[{
                "name": "calculator", "args": {"expression": m.group(1)}, "id": f"call_{uuid.uuid4().hex[:8]}"}])
        return AIMessage(content=f"（假模型）我收到了：{text}。试试问我天气或算术题吧！")

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._decide(messages))])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs) -> Iterator[ChatGenerationChunk]:
        msg = self._decide(messages)
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            import json
            yield ChatGenerationChunk(message=AIMessageChunk(content="", tool_call_chunks=[{
                "name": tc["name"], "args": json.dumps(tc["args"], ensure_ascii=False),
                "id": tc["id"], "index": 0}]))
            return
        for ch in msg.content:  # 逐字"流式"输出
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=ch))
            if run_manager:
                run_manager.on_llm_new_token(ch, chunk=chunk)
            yield chunk


def get_model():
    """有 LG_MODEL 环境变量就用真模型，否则用假模型。"""
    name = os.environ.get("LG_MODEL")
    if name:
        from langchain.chat_models import init_chat_model  # 需要 pip install langchain
        return init_chat_model(name)
    return FakeToolModel()
