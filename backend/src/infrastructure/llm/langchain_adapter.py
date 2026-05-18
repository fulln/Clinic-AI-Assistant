import os
from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class LLMAdapter:
    def __init__(self) -> None:
        self._client = ChatOpenAI(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            openai_api_base=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            streaming=True,
            temperature=0.7,
        )

    async def astream(self, messages: list[dict]) -> AsyncIterator[str]:
        lc_messages: list[BaseMessage] = []
        for m in messages:
            role, content = m["role"], m["content"]
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            else:
                lc_messages.append(AIMessage(content=content))

        async for chunk in self._client.astream(lc_messages):
            if chunk.content:
                yield chunk.content

    async def ainvoke(self, messages: list[dict]) -> str:
        lc_messages: list[BaseMessage] = []
        for m in messages:
            role, content = m["role"], m["content"]
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            else:
                lc_messages.append(AIMessage(content=content))
        result = await self._client.ainvoke(lc_messages)
        return result.content
