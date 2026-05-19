import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class CreateAgentRequest(BaseModel):
    name: str
    slug: str
    description: str
    agent_type: str
    capabilities: list[str] = []
    allowed_roles: list[str] = []
    workflow_config: dict = {}
    system_prompt_en: Optional[str] = None
    system_prompt_zh: Optional[str] = None
    tools: list[str] = []
    max_tool_turns: int = 3
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$", v):
            raise ValueError("slug must be lowercase alphanumeric with hyphens")
        return v


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    agent_type: str
    capabilities: list[str]
    allowed_roles: list[str]
    status: str
    version: Optional[str] = None
    system_prompt_en: Optional[str] = None
    system_prompt_zh: Optional[str] = None
    tools: list[str] = []
    max_tool_turns: int = 3
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None

    model_config = {"from_attributes": True}


class BatchPublishRequest(BaseModel):
    agents: list[CreateAgentRequest]

    @field_validator("agents")
    @classmethod
    def max_fifty_items(cls, v: list) -> list:
        if len(v) > 50:
            raise ValueError("Batch may contain at most 50 agents")
        if len(v) == 0:
            raise ValueError("Batch must contain at least one agent")
        return v


class BatchPublishResponse(BaseModel):
    batch_id: uuid.UUID
    status: str
    total_count: int
    submitted_at: datetime


class BatchStatusItem(BaseModel):
    index: int
    status: str
    agent_id: Optional[uuid.UUID] = None
    error: Optional[str] = None


class BatchStatusResponse(BaseModel):
    batch_id: uuid.UUID
    status: str
    total_count: int
    success_count: int
    failure_count: int
    items: list[BatchStatusItem]
