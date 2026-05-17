import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None


class SessionInfo(BaseModel):
    id: uuid.UUID
    active_agent_id: Optional[uuid.UUID] = None
    rag_enabled: bool = False


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    user_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    active_agent_id: Optional[uuid.UUID] = None
    rag_enabled: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: uuid.UUID
    title: str
    active_agent_id: Optional[uuid.UUID] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationListItem]
    total: int


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    agent_id: Optional[uuid.UUID] = None
    has_disclaimer: bool = False
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    session: SessionInfo
    messages: list[MessageResponse]


class SendMessageRequest(BaseModel):
    content: str
    agent_id: Optional[uuid.UUID] = None
    rag_enabled: Optional[bool] = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content cannot be empty")
        if len(v) > 4000:
            raise ValueError("content exceeds 4000 characters")
        return v


class SessionUpdateRequest(BaseModel):
    active_agent_id: Optional[uuid.UUID] = None
    rag_enabled: Optional[bool] = None
