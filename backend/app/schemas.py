from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

Role = str  # pm | qa | legal


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "pm"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    role: str
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str = "新会话"
    role: str = "pm"


class Citation(BaseModel):
    document: str
    snippet: str
    score: float = 0.0


class RiskItem(BaseModel):
    risk_level: str = Field(description="high | medium | low | compliant")
    location: str = ""
    verdict: str = ""
    suggestion: str = ""
    citations: list[Citation] = []


class ReviewResult(BaseModel):
    summary: str = ""
    items: list[RiskItem] = []


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    role: str = "pm"
    message: str
    document_ids: list[int] = []


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    mime: str
    kind: str
    parse_status: str
    summary: str
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    attachments: list | None = None
    review_result: dict | None = None
    created_at: datetime
