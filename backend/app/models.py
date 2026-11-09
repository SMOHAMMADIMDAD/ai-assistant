import enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum
from .database import Base

# FIX: Define a case-insensitive enum to prevent errors
class CaseInsensitiveEnum(Enum):
    def __init__(self, enum_type, **kwargs):
        self.enum_type = enum_type
        self._name_map = {item.name.lower(): item for item in enum_type}
        super().__init__(enum_type, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.upper()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._name_map.get(value.lower(), None)

class MessageRole(str, enum.Enum):
    USER = "user"
    MODEL = "model"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    custom_instruction = Column(Text, nullable=True)
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    system_prompt = Column(Text)
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    # FIX: Use the case-insensitive enum type
    role = Column(CaseInsensitiveEnum(MessageRole), nullable=False)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")
