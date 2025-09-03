from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.repository.chatRepo import ChatSessionRepository, MessageRepository
from app.db.models.chat import ChatSession
from app.db.schema.chat import (
    ChatSessionInCreate,
    ChatSessionInUpdate,
    ChatSessionOutput,
    MessageOutput,
    MessageInCreateBody,
    MessageInCreate,
    MessageInUpdate,
)


class ChatSessionService:
    def __init__(self, session: Session):
        self._sessions = ChatSessionRepository(session=session)
        self._messages = MessageRepository(session=session)

    # --- Sessions ---
    def create_session(self, payload: ChatSessionInCreate) -> ChatSessionOutput:
        created = self._sessions.create_session(data=payload)
        return created

    def get_session(self, session_id: int) -> ChatSessionOutput:
        sess = self._sessions.get_session_by_id(session_id=session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return sess

    def list_sessions_by_user(
        self, user_id: int, limit: int = 20, offset: int = 0, newest_first: bool = True
    ) -> List[ChatSessionOutput]:
        return self._sessions.list_sessions_by_user(
            user_id=user_id, limit=limit, offset=offset, newest_first=newest_first
        )

    def update_session(self, session_id: int, payload: ChatSessionInUpdate) -> ChatSessionOutput:
        sess = self._sessions.get_session_by_id(session_id=session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Chat session not found")

        if payload.name is not None and payload.name.strip() != "":
            updated = self._sessions.rename_session(session_id=session_id, new_name=payload.name.strip())
            return updated

        return sess

    def delete_session(self, session_id: int) -> None:
        ok = self._sessions.delete_session(session_id=session_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Chat session not found")

    # --- Messages ---
    def list_messages_for_session(
        self, session_id: int, limit: int = 100, offset: int = 0, ascending: bool = True
    ) -> List[MessageOutput]:
        if not self._sessions.session_exists(session_id=session_id):
            raise HTTPException(status_code=404, detail="Chat session not found")
        return self._messages.list_messages_by_session(
            session_id=session_id, limit=limit, offset=offset, ascending=ascending
        )

    def create_message(self, session_id: int, payload: MessageInCreateBody) -> MessageOutput:
        if not self._sessions.session_exists(session_id=session_id):
            raise HTTPException(status_code=404, detail="Chat session not found")
        msg_in = MessageInCreate(session_id=session_id, role=payload.role, content=payload.content)
        created = self._messages.create_message(data=msg_in)  # auto-title handled in repo
        return created

    def get_session_with_messages(self, session_id: int) -> ChatSessionOutput:
        sess = (
            self._sessions.session.query(ChatSession)
            .options(selectinload(ChatSession.messages))
            .filter(ChatSession.id == session_id)
            .first()
        )
        if not sess:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return sess

    def delete_message(self, session_id: int, message_id: int) -> None:
        if not self._sessions.session_exists(session_id=session_id):
            raise HTTPException(status_code=404, detail="Chat session not found")

        msg = self._messages.get_message_by_id(message_id=message_id)
        if not msg or msg.session_id != session_id:
            raise HTTPException(status_code=404, detail="Message not found in this session")

        ok = self._messages.delete_message(message_id=message_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Message already deleted")

    def update_message(self, message_id: int, payload: MessageInUpdate) -> MessageOutput:
        if payload.role is None and payload.content is None:
            raise HTTPException(status_code=400, detail="Nothing to update")

        updated = self._messages.update_message(
            message_id=message_id,
            role=payload.role,
            content=payload.content,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Message not found")
        return updated
