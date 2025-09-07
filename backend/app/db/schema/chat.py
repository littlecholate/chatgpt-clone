from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ---------- Message Schemas ----------
class MessageBase(BaseModel):
    role: str
    content: str


class MessageIn(BaseModel):
    content: str
    mode: int

    
class MessageInCreate(MessageBase):
    session_id: int


class MessageInCreateBody(BaseModel):
    role: str
    content: str


class MessageInUpdate(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class MessageOutput(MessageBase):
    id: int
    session_id: int
    create_date: datetime

    class Config:
        orm_mode = True


# ---------- Chat Session Schemas ----------
class ChatSessionBase(BaseModel):
    user_id: int
    name: Optional[str] = "New Chat"  # DB also defaults to "New Chat"


class ChatSessionInCreate(ChatSessionBase):
    pass


class ChatSessionInUpdate(BaseModel):
    name: Optional[str] = None


class ChatSessionOutput(ChatSessionBase):
    id: int
    name: str
    create_date: datetime
    messages: List[MessageOutput] = []

    class Config:
        orm_mode = True
