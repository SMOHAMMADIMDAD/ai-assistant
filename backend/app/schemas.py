from pydantic import BaseModel, EmailStr, constr, ConfigDict
from datetime import datetime
from typing import Optional, List
from .models import MessageRole

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: constr(min_length=10, max_length=15)
    password: str
    confirm_password: str

class UserPublic(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    sessions_count: int
    custom_instruction: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Token Schemas
class TokenRequest(BaseModel):
    identifier: str # Can be email or phone number
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Chat Schemas
class ChatMessagePublic(BaseModel):
    role: MessageRole
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatSessionDetail(BaseModel):
    session_id: int
    title: str
    history: List[ChatMessagePublic]
    model_config = ConfigDict(from_attributes=True)

class ChatSessionInfo(BaseModel):
    id: int
    title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    response: str
    session_id: int
    title: str
    sources: List[dict]

class CustomInstructionUpdate(BaseModel):
    instruction: str

class SessionRenameRequest(BaseModel):
    title: str
