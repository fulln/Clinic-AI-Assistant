import json
import os
import uuid
from typing import AsyncIterator

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

from src.infrastructure.llm.tools.base import ToolContext, ToolDefinition, ToolEvent


class LLMAdapter:
    def __init__(self) -> None:
        self._default_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._api_base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._client = ChatOpenAI(
            model=self._default_model,
            openai_api_key=self._api_key,
            openai_api_base=self._api_base,
            streaming=True,
            temperature=0.7,
        )

    def _resolve_client(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatOpenAI:
        # Fast path: no overrides
        if model is None and temperature is None and max_tokens is None:
            return self._client
        kwargs = {
            "model": model or self._default_model,
            "openai_api_key": self._api_key,
            "openai_api_base": self._api_base,
            "streaming": True,
            "temperature": temperature if temperature is not None else 0.7,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)

    @staticmethod
    def _to_lc_messages(messages: list[dict]) -> list[BaseMessage]:
        lc_messages: list[BaseMessage] = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "tool":
                lc_messages.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=m.get("tool_call_id", ""),
                    )
                )
            elif role == "assistant":
                tool_calls = m.get("tool_calls") or []
                if tool_calls:
                    lc_messages.append(
                        AIMessage(
                            content=content or "",
                            tool_calls=[
                                {
                                    "id": tc["id"],
                                    "name": tc["name"],
                                    "args": tc.get("args") or {},
                                }
                                for tc in tool_calls
                            ],
                        )
                    )
                else:
                    lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(AIMessage(content=content))
        return lc_messages

    async def astream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        client = self._resolve_client(model, temperature, max_tokens)
        async for chunk in client.astream(self._to_lc_messages(messages)):
            if chunk.content:
                yield chunk.content

    async def ainvoke(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        client = self._resolve_client(model, temperature, max_tokens)
        result = await client.ainvoke(self._to_lc_messages(messages))
        return result.content

    async def astream_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        tool_context: ToolContext,
        *,
        max_tool_turns: int = 3,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[ToolEvent | str]:
        """Run a tool-calling loop, then stream the final assistant reply.

        Yields:
          - `ToolEvent` after each tool call completes (one per call), so the
            caller can emit UI progress.
          - `str` tokens for the final assistant response.

        If `tools` is empty, this falls back to plain streaming on the input
        messages — equivalent to `astream`.
        """
        if not tools:
            async for token in self.astream(messages, model, temperature, max_tokens):
                yield token
            return

        client = self._resolve_client(model, temperature, max_tokens)
        bound = client.bind_tools([t.to_openai_spec() for t in tools])
        tools_by_name = {t.name: t for t in tools}

        working_messages = list(messages)

        for _turn in range(max_tool_turns):
            lc_messages = self._to_lc_messages(working_messages)
            ai_msg = await bound.ainvoke(lc_messages)
            tool_calls = getattr(ai_msg, "tool_calls", None) or []

            if not tool_calls:
                # No more tool calls — stream the final answer.
                # We re-run astream on the same messages to get token chunks
                # instead of using ai_msg.content (which is already complete).
                async for chunk in bound.astream(lc_messages):
                    if chunk.content:
                        yield chunk.content
                return

            # Record the assistant tool-call turn for the next round.
            working_messages.append(
                {
                    "role": "assistant",
                    "content": ai_msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.get("id") or str(uuid.uuid4()),
                            "name": tc["name"],
                            "args": tc.get("args") or {},
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                call_id = tc.get("id") or str(uuid.uuid4())
                name = tc["name"]
                args = tc.get("args") or {}
                tool = tools_by_name.get(name)
                # Snapshot artifacts produced by this call only.
                before = len(tool_context.collected_artifacts)
                if tool is None:
                    result_text = f"Tool '{name}' is not available."
                else:
                    try:
                        result_text = await tool.handler(args, tool_context)
                    except Exception as exc:  # noqa: BLE001 — surface to LLM
                        result_text = f"Tool '{name}' failed: {exc}"
                new_artifacts = tool_context.collected_artifacts[before:]

                working_messages.append(
                    {
                        "role": "tool",
                        "content": result_text,
                        "tool_call_id": call_id,
                    }
                )

                yield ToolEvent(
                    name=name,
                    arguments=args,
                    result=result_text,
                    artifacts=list(new_artifacts),
                )

            # If every tool the LLM called this turn has signalled exhaustion
            # (e.g. RAG returned empty), don't let it burn the remaining turns
            # retrying the same dead end. Drop tools and stream a final reply.
            if tool_calls and all(
                tc["name"] in tool_context.exhausted_tools for tc in tool_calls
            ):
                async for chunk in client.astream(self._to_lc_messages(working_messages)):
                    if chunk.content:
                        yield chunk.content
                return

        # Hit the loop cap. Force a final answer with tools disabled so the
        # LLM uses whatever context it gathered so far.
        async for chunk in client.astream(self._to_lc_messages(working_messages)):
            if chunk.content:
                yield chunk.content
