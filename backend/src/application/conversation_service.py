"""ConversationApplicationService: orchestrates message flow with SSE streaming."""
import json
import time
import uuid
from dataclasses import dataclass
from typing import AsyncIterator

from fastapi import HTTPException, status

from src.domains.agent.entities import Agent
from src.domains.agent.repository import IAgentRepository
from src.domains.agent.services import AgentDispatcher
from src.domains.audit.entities import AuditAction, AuditOutcome
from src.domains.audit.services import AuditService
from src.domains.conversation.entities import Conversation, ConversationSession, Locale
from src.domains.conversation.i18n import (
    get_conversation_not_found_message,
    get_disclaimer,
    get_forbidden_agent_message,
    get_generic_error_message,
    get_progress_message,
    parse_locale,
)
from src.domains.conversation.repository import IConversationRepository
from src.domains.conversation.services import ConversationDomainService
from src.domains.rag.repository import IKnowledgeBaseRepository
from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.tools.base import ToolContext, ToolEvent


@dataclass
class OrchestraStep:
    agent: Agent
    reason: str


class ConversationApplicationService:
    def __init__(
        self,
        conv_repo: IConversationRepository,
        agent_repo: IAgentRepository,
        audit: AuditService,
        rag_repo: IKnowledgeBaseRepository | None = None,
    ) -> None:
        self._conv_repo = conv_repo
        self._agent_repo = agent_repo
        self._rag_repo = rag_repo
        self._audit = audit
        self._llm = LLMAdapter()
        self._dispatcher = AgentDispatcher(self._llm)
        self._domain = ConversationDomainService()

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        title: str | None,
        agent_id: uuid.UUID | None,
        locale: Locale,
    ) -> tuple[Conversation, ConversationSession]:
        conv = self._domain.create_conversation(user_id, title, locale)
        session = self._domain.create_session(conv.id, agent_id, locale)
        await self._conv_repo.save_conversation(conv)
        await self._conv_repo.save_session(session)
        return conv, session

    async def get_conversations(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Conversation], int]:
        return await self._conv_repo.find_by_user_id(user_id, page, page_size)

    async def get_conversation_detail(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, limit: int, before_id: uuid.UUID | None
    ):
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        session = await self._conv_repo.find_session(conversation_id)
        messages = await self._conv_repo.get_messages(conversation_id, limit, before_id)
        return conv, session, messages

    async def stream_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        agent_id: uuid.UUID | None,
        rag_enabled: bool | None,
        locale: Locale | None,
        user_role: str,
    ) -> AsyncIterator[str]:
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        requested_locale = parse_locale(locale)
        if not conv or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_conversation_not_found_message(requested_locale),
            )

        session = await self._conv_repo.find_session(conversation_id)
        if not session:
            session = self._domain.create_session(conv.id, locale=requested_locale)
            await self._conv_repo.save_session(session)
        effective_locale = parse_locale(locale or session.locale)
        session.set_locale(effective_locale)

        effective_agent_id = agent_id or session.active_agent_id
        forced_agent = None
        if effective_agent_id:
            forced_agent = await self._agent_repo.find_by_id(effective_agent_id)
            if forced_agent and user_role not in forced_agent.allowed_roles and user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=get_forbidden_agent_message(effective_locale),
                )

        if rag_enabled is not None:
            session.rag_enabled = rag_enabled

        # Save user message
        user_msg = self._domain.build_user_message(conv.id, session.id, content, effective_locale)
        await self._conv_repo.save_message(user_msg)
        # Streaming responses outlive FastAPI's dependency cleanup, so we
        # commit here ourselves — otherwise the user message would be lost
        # if the client disconnects mid-stream.
        await self._conv_repo.commit()

        # Build message history for LLM
        history = await self._conv_repo.get_messages(conv.id, 20, None)
        messages_for_llm = [{"role": m.role.value, "content": m.content} for m in history]

        message_id = str(uuid.uuid4())
        start_ts = time.monotonic()

        # SSE: start event
        yield (
            "event: start\ndata: "
            f"{json.dumps({'message_id': message_id, 'agent_id': str(effective_agent_id) if effective_agent_id else None, 'session_id': str(session.id), 'locale': effective_locale.value})}\n\n"
        )

        full_response = []
        refused = False
        steps: list[OrchestraStep] = []
        try:
            progress = self._progress
            yield progress(
                effective_locale,
                "supervisor",
                get_progress_message("supervisor_start", effective_locale),
            )

            steps = await self._build_orchestra_steps(
                content=content,
                messages=messages_for_llm,
                forced_agent=forced_agent,
                user_role=user_role,
                rag_enabled=session.rag_enabled,
                locale=effective_locale,
            )
            if not steps:
                raise ValueError(get_generic_error_message(effective_locale))

            step_labels = "、".join(step.agent.name for step in steps)
            yield progress(
                effective_locale,
                "routing",
                get_progress_message("routing", effective_locale, step_labels=step_labels),
            )

            child_outputs: list[dict] = []
            for index, step in enumerate(steps, start=1):
                yield progress(
                    effective_locale,
                    "child_start",
                    get_progress_message(
                        "child_start",
                        effective_locale,
                        index=index,
                        total=len(steps),
                        agent_name=step.agent.name,
                        workflow_type=step.agent.slug,
                    ),
                    agent_id=str(step.agent.id),
                    agent_name=step.agent.name,
                    workflow_type=step.agent.slug,
                )

                tool_ctx = ToolContext(
                    user_id=user_id,
                    user_role=user_role,
                    locale=effective_locale,
                    rag_repo=self._rag_repo,
                )
                stream = await self._dispatcher.dispatch(
                    agent=step.agent,
                    messages=messages_for_llm,
                    session_context=session.context_snapshot,
                    user_role=user_role,
                    locale=effective_locale,
                    tool_context=tool_ctx,
                )
                # Single-step routing: stream child tokens straight to the client.
                # This keeps the agent's configured prompt/voice intact (the
                # supervisor summary step would otherwise rewrite the reply).
                single_step = len(steps) == 1
                child_tokens: list[str] = []
                async for item in stream:
                    if isinstance(item, ToolEvent):
                        if single_step:
                            yield progress(
                                effective_locale,
                                "tool_call",
                                get_progress_message(
                                    "tool_call",
                                    effective_locale,
                                    agent_name=step.agent.name,
                                    tool_name=item.name,
                                ),
                                agent_id=str(step.agent.id),
                                agent_name=step.agent.name,
                                workflow_type=step.agent.slug,
                                artifacts=item.artifacts,
                            )
                        continue
                    # Plain token from LLM
                    child_tokens.append(item)
                    if single_step:
                        full_response.append(item)
                        yield f"event: token\ndata: {json.dumps({'token': item})}\n\n"
                child_text = "".join(child_tokens)
                child_outputs.append(
                    {
                        "agent_id": str(step.agent.id),
                        "agent_name": step.agent.name,
                        "agent_slug": step.agent.slug,
                        "reason": step.reason,
                        "output": child_text,
                    }
                )
                yield progress(
                    effective_locale,
                    "child_done",
                    get_progress_message(
                        "child_done",
                        effective_locale,
                        agent_name=step.agent.name,
                    ),
                    agent_id=str(step.agent.id),
                    agent_name=step.agent.name,
                    workflow_type=step.agent.slug,
                )

            # Only synthesize through the supervisor when multiple child agents ran.
            if len(steps) > 1:
                yield progress(
                    effective_locale,
                    "supervisor",
                    get_progress_message("supervisor_summary", effective_locale),
                )
                async for token in self._stream_supervisor_answer(
                    content,
                    messages_for_llm,
                    child_outputs,
                    effective_locale,
                ):
                    full_response.append(token)
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            response_text = "".join(full_response)
            disclaimer_text = get_disclaimer(effective_locale)
            if disclaimer_text not in response_text:
                disclaimer_token = f"\n\n{disclaimer_text}"
                full_response.append(disclaimer_token)
                yield f"event: token\ndata: {json.dumps({'token': disclaimer_token})}\n\n"
        except HTTPException:
            raise
        except Exception:
            import traceback
            traceback.print_exc()
            refused = True
            yield (
                "event: error\ndata: "
                f"{json.dumps({'code': 'agent_error', 'message': get_generic_error_message(effective_locale), 'locale': effective_locale.value})}\n\n"
            )

        if not refused:
            response_text = "".join(full_response)
            disclaimer_text = get_disclaimer(effective_locale)
            if disclaimer_text in response_text:
                yield (
                    "event: disclaimer\ndata: "
                    f"{json.dumps({'text': disclaimer_text, 'locale': effective_locale.value})}\n\n"
                )

            latency_ms = round((time.monotonic() - start_ts) * 1000)
            yield (
                "event: end\ndata: "
                f"{json.dumps({'message_id': message_id, 'latency_ms': latency_ms, 'locale': effective_locale.value})}\n\n"
            )

            # Save assistant message
            response_agent_id = steps[0].agent.id if steps else effective_agent_id
            if response_agent_id:
                assistant_msg = self._domain.build_assistant_message(
                    conv.id,
                    session.id,
                    response_agent_id,
                    response_text,
                    effective_locale,
                    metadata={"latency_ms": latency_ms, "orchestra": True},
                )
                await self._conv_repo.save_message(assistant_msg)

        session.touch()
        await self._conv_repo.save_session(session)
        # Commit assistant message + session-touch together at the end of
        # the stream; see the comment after save_user_message above.
        await self._conv_repo.commit()

        await self._audit.log(
            action=AuditAction.MESSAGE_SENT if not refused else AuditAction.MESSAGE_REFUSED,
            resource_type="Message",
            outcome=AuditOutcome.SUCCESS if not refused else AuditOutcome.REFUSED,
            actor_id=user_id,
            actor_role=user_role,
            session_id=session.id,
            detail={"locale": effective_locale.value},
        )

    @staticmethod
    def _progress(
        locale: Locale,
        stage: str,
        message: str,
        agent_id: str | None = None,
        agent_name: str | None = None,
        workflow_type: str | None = None,
        artifacts: list[dict] | None = None,
    ) -> str:
        payload = {
            "stage": stage,
            "message": message,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "workflow_type": workflow_type,
            "artifacts": artifacts or [],
            "locale": locale.value,
        }
        return f"event: progress\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def _build_orchestra_steps(
        self,
        content: str,
        messages: list[dict],
        forced_agent: Agent | None,
        user_role: str,
        rag_enabled: bool,
        locale: Locale,
    ) -> list[OrchestraStep]:
        if forced_agent:
            return [
                OrchestraStep(
                    forced_agent,
                    get_progress_message("user_selected", locale),
                )
            ]

        candidates = [
            agent
            for agent in await self._agent_repo.find_all()
            if agent.status.value == "published"
            and (user_role == "admin" or user_role in agent.allowed_roles)
            and agent.agent_type.value == "formal"
        ]
        if not candidates:
            return []

        route = await self._route_with_supervisor(content, messages, candidates, rag_enabled, locale)
        selected: list[OrchestraStep] = []
        by_id = {str(agent.id): agent for agent in candidates}
        by_slug = {agent.slug: agent for agent in candidates}

        for item in route:
            raw = str(item.get("agent_id") or item.get("slug") or item.get("workflow_type") or "")
            agent = by_id.get(raw) or by_slug.get(raw)
            if agent and all(step.agent.id != agent.id for step in selected):
                selected.append(
                    OrchestraStep(
                        agent=agent,
                        reason=str(item.get("reason") or get_progress_message("supervisor_route", locale)),
                    )
                )
            if len(selected) >= 2:
                break

        if selected:
            return selected

        # Fallback: when supervisor produced nothing, pick the first RAG-enabled
        # agent if user message mentions knowledge-base, else the first candidate.
        text = content.lower()
        fallback_agent: Agent | None = None
        if rag_enabled or "知识库" in text or "rag" in text:
            fallback_agent = next((a for a in candidates if "knowledge_base_search" in a.tools), None)
        fallback_agent = fallback_agent or candidates[0]
        return [
            OrchestraStep(
                fallback_agent,
                get_progress_message("fallback_route", locale),
            )
        ]

    async def _route_with_supervisor(
        self,
        content: str,
        messages: list[dict],
        candidates: list[Agent],
        rag_enabled: bool,
        locale: Locale,
    ) -> list[dict]:
        catalog = [
            {
                "agent_id": str(agent.id),
                "slug": agent.slug,
                "name": agent.name,
                "description": agent.description,
                "tools": agent.tools,
            }
            for agent in candidates
        ]
        recent = messages[-6:]
        prompt = self._build_supervisor_route_prompt(content, recent, catalog, rag_enabled, locale)
        try:
            result = await self._llm.ainvoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "You only output valid JSON."
                            if locale == Locale.EN_US
                            else "你只输出可解析 JSON。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            parsed = json.loads(result.strip())
            if isinstance(parsed, dict):
                parsed = parsed.get("agents", [])
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except Exception:
            return []
        return []

    async def _stream_supervisor_answer(
        self,
        content: str,
        messages: list[dict],
        child_outputs: list[dict],
        locale: Locale,
    ) -> AsyncIterator[str]:
        summary_prompt = self._build_supervisor_summary_prompt(content, messages, child_outputs, locale)
        async for token in self._llm.astream(
            [
                {
                    "role": "system",
                    "content": (
                        "You are the supervisor agent responsible for synthesizing child-agent outputs into the final reply."
                        if locale == Locale.EN_US
                        else "你是负责汇总子 agent 输出的主控 agent。"
                    ),
                },
                {"role": "user", "content": summary_prompt},
            ]
        ):
            yield token

    async def update_session(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        active_agent_id: uuid.UUID | None,
        rag_enabled: bool | None,
        locale: Locale | None,
        user_role: str,
    ) -> ConversationSession:
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        requested_locale = parse_locale(locale)
        if not conv or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_conversation_not_found_message(requested_locale),
            )
        session = await self._conv_repo.find_session(conversation_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_conversation_not_found_message(requested_locale),
            )
        if active_agent_id is not None:
            session.switch_agent(active_agent_id)
        if rag_enabled is not None:
            session.rag_enabled = rag_enabled
        if locale is not None:
            session.set_locale(requested_locale)
        await self._conv_repo.save_session(session)
        return session

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        await self._conv_repo.soft_delete_conversation(conversation_id)

    @staticmethod
    def _build_supervisor_route_prompt(
        content: str,
        recent: list[dict],
        catalog: list[dict],
        rag_enabled: bool,
        locale: Locale,
    ) -> str:
        if locale == Locale.EN_US:
            return (
                "You are the supervisor agent for a clinic multi-agent system. "
                "Select the best 1 child agent for the user's latest request, or 2 only when the request clearly needs two distinct capabilities. "
                "Pick agents based on each candidate's description. "
                "Output JSON only, an array where each item contains agent_id and reason. "
                "Write the reasons in English.\n\n"
                f"RAG enabled on session: {rag_enabled}\n"
                f"Available child agents (each has agent_id, slug, name, description, rag_enabled): "
                f"{json.dumps(catalog, ensure_ascii=False)}\n"
                f"Shared conversation context: {json.dumps(recent, ensure_ascii=False)}\n"
                f"Latest user request: {content}"
            )
        return (
            "你是诊所多智能体系统的主控 agent。根据用户最新问题和共享对话上下文，"
            "从候选 agent 中选择最合适的 1 个；只有当问题明显需要两个不同能力时才选择 2 个。"
            "请基于每个 agent 的 description 来判断。"
            "只输出 JSON 数组，不要输出 Markdown。每项包含 agent_id 和 reason。\n\n"
            f"会话 RAG 是否启用：{rag_enabled}\n"
            f"可用子 agent（每项含 agent_id、slug、name、description、rag_enabled）："
            f"{json.dumps(catalog, ensure_ascii=False)}\n"
            f"共享对话上下文：{json.dumps(recent, ensure_ascii=False)}\n"
            f"用户最新问题：{content}"
        )

    @staticmethod
    def _build_supervisor_summary_prompt(
        content: str,
        messages: list[dict],
        child_outputs: list[dict],
        locale: Locale,
    ) -> str:
        if locale == Locale.EN_US:
            return (
                "You are the supervisor agent of a clinic multi-agent system. "
                "The user-facing reply must be written in English, regardless of the language used in prior messages. "
                "Based on the shared context and child-agent outputs, write the final user reply. "
                "Requirements: synthesize instead of concatenating, explain the key takeaways, keep the medical safety boundary, and do not expose internal JSON.\n\n"
                f"Latest user request: {content}\n"
                f"Shared conversation context: {json.dumps(messages[-8:], ensure_ascii=False)}\n"
                f"Child-agent outputs: {json.dumps(child_outputs, ensure_ascii=False)}"
            )
        return (
            "你是诊所多智能体系统的主控 agent。你已经把用户问题分派给子 agent 执行。"
            "请基于共享用户提示词、上下文和子 agent 输出，生成给前端用户的最终回复。"
            "要求：整合而不是机械拼接；说明关键结论；保留医疗安全边界；不要暴露内部 JSON。\n\n"
            f"用户最新问题：{content}\n"
            f"共享对话上下文：{json.dumps(messages[-8:], ensure_ascii=False)}\n"
            f"子 agent 执行结果：{json.dumps(child_outputs, ensure_ascii=False)}"
        )
