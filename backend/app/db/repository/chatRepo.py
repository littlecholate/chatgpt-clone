from __future__ import annotations
from typing import List, Optional

from sqlalchemy import func, desc, asc

from .base import BaseRepository
from app.db.models.chat import ChatSession, Message
from app.db.schema.chat import ChatSessionInCreate, MessageInCreate

DEFAULT_SESSION_NAME = "New Chat"
SNIPPET_LEN = 10


class ChatSessionRepository(BaseRepository):
    def create_session(self, data: ChatSessionInCreate) -> ChatSession:
        new_session = ChatSession(**data.model_dump(exclude_none=True))
        self.session.add(new_session)
        self.session.commit()
        self.session.refresh(new_session)
        return new_session

    def get_session_by_id(self, session_id: int) -> Optional[ChatSession]:
        return (
            self.session.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

    def list_sessions_by_user(
        self, user_id: int, limit: int = 20, offset: int = 0, newest_first: bool = True
    ) -> List[ChatSession]:
        q = self.session.query(ChatSession).filter(ChatSession.user_id == user_id)
        q = q.order_by(desc(ChatSession.create_date) if newest_first else asc(ChatSession.create_date))
        return q.offset(offset).limit(limit).all()

    def rename_session(self, session_id: int, new_name: str) -> Optional[ChatSession]:
        session_obj = (
            self.session.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )
        if not session_obj:
            return None
        session_obj.name = new_name
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def delete_session(self, session_id: int) -> bool:
        session_obj = (
            self.session.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )
        if not session_obj:
            return False
        self.session.delete(session_obj)
        self.session.commit()
        return True

    def session_exists(self, session_id: int) -> bool:
        return (
            self.session.query(ChatSession.id)
            .filter(ChatSession.id == session_id)
            .first()
            is not None
        )

    def count_messages(self, session_id: int) -> int:
        return (
            self.session.query(func.count(Message.id))
            .filter(Message.session_id == session_id)
            .scalar()
            or 0
        )


class MessageRepository(BaseRepository):
    def create_message(self, data: MessageInCreate) -> Message:
        session_obj = (
            self.session.query(ChatSession)
            .filter(ChatSession.id == data.session_id)
            .first()
        )
        if not session_obj:
            raise ValueError(f"ChatSession {data.session_id} not found")

        existing_count = (
            self.session.query(func.count(Message.id))
            .filter(Message.session_id == data.session_id)
            .scalar()
            or 0
        )

        new_msg = Message(**data.model_dump(exclude_none=True))
        self.session.add(new_msg)
        self.session.commit()
        self.session.refresh(new_msg)

        # Auto-title from first message
        if existing_count == 0 and (not session_obj.name or session_obj.name == DEFAULT_SESSION_NAME):
            snippet = (new_msg.content or "").strip()[:SNIPPET_LEN]
            if snippet:
                session_obj.name = snippet
                self.session.commit()
                self.session.refresh(session_obj)

        return new_msg

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        return (
            self.session.query(Message)
            .filter(Message.id == message_id)
            .first()
        )

    def list_messages_by_session(
        self,
        session_id: int,
        limit: int = 100,
        offset: int = 0,
        ascending: bool = True,
    ) -> List[Message]:
        q = self.session.query(Message).filter(Message.session_id == session_id)
        q = q.order_by(asc(Message.create_date) if ascending else desc(Message.create_date))
        return q.offset(offset).limit(limit).all()

    def get_last_message(self, session_id: int) -> Optional[Message]:
        return (
            self.session.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(desc(Message.create_date))
            .first()
        )

    def delete_message(self, message_id: int) -> bool:
        msg = self.session.query(Message).filter(Message.id == message_id).first()
        if not msg:
            return False
        self.session.delete(msg)
        self.session.commit()
        return True

    def update_message(self, message_id: int, *, role: Optional[str] = None, content: Optional[str] = None) -> Optional[Message]:
        msg = (
            self.session.query(Message)
            .filter(Message.id == message_id)
            .first()
        )
        if not msg:
            return None

        changed = False
        if role is not None and role.strip() != "":
            msg.role = role.strip()
            changed = True
        if content is not None and content.strip() != "":
            msg.content = content
            changed = True

        if changed:
            self.session.commit()
            self.session.refresh(msg)
        return msg
