from typing import Generator, List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from contextlib import suppress
import httpx

from app.tools.web_search_hook import web_search_summary       # (NEW)
from app.tools.search_gate import should_search                # (NEW)
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

ROBOT_ENDPOINT = "http://localhost:8000/v1/chat/completions"
ROBOT_MODEL = "Qwen/Qwen3-0.6B"

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

    def stream_user_and_robot_message(
        self, session_id: int, user_text: str, force_search: bool | None = None,
    ) -> Generator[str, None, None]:
        """
        - Save user msg
        - Call robot endpoint with history + user input
        - Yield tokens as SSE
        - Save final robot msg
        """

        # 1. Save user msg
        if not self._sessions.session_exists(session_id=session_id):
            raise HTTPException(status_code=404, detail="Chat session not found")
        msg_in = MessageInCreate(session_id=session_id, role="user", content=user_text)
        self._messages.create_message(data=msg_in)  # auto-title handled in repo

        # 2. Build history including system prompt
        history = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Do not reveal hidden reasoning. "
                    "If web results are provided below, prefer them for facts and cite links in markdown."
                ),
            }
        ]
        """Convert DB messages to [{role, content}, ...]."""
        msgs = self._messages.list_messages_by_session(
            session_id=session_id, limit=100, offset=0, ascending=True
        )
        history.extend([{"role": m.role, "content": m.content} for m in msgs])

        # 2a) (NEW) Web search pre-hook (heuristic or force)
        do_search = force_search if force_search is not None else should_search(user_text)
        if do_search:
            search_md = web_search_summary(user_text, max_results=5)
            if search_md:
                # Keep it as a separate system message to avoid polluting the user text.
                history.append({
                    "role": "system",
                    "content": (
                        "Web results (use if relevant; cite the links you rely on):\n\n"
                        f"{search_md}"
                    ),
                })

        # 3. Prepare request payload
        payload = {
            "model": ROBOT_MODEL,
            "messages": history,
            "chat_template_kwargs": {"enable_thinking": False},
            "stream": True,
        }

        pieces: List[str] = []

        try:
            # 4. Stream from robot with httpx
            with httpx.stream("POST", ROBOT_ENDPOINT, json=payload, timeout=None) as r:
                # r.iter_lines already return strings
                for line in r.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data = line[len("data: "):]
                        if data.strip() == "[DONE]":
                            break

                        import json
                        obj = json.loads(data)
                        delta = obj["choices"][0]["delta"].get("content")
                        if delta:
                            pieces.append(delta)
                            yield f"data:{delta}\n\n"

            final_text = "".join(pieces).strip()

            # 5. Save robot msg
            msg_in = MessageInCreate(session_id=session_id, role="robot", content=final_text)
            self._messages.create_message(data=msg_in)  # auto-title handled in repo

            yield "event:done\ndata:ok\n\n"

        finally:
            with suppress(Exception):
                pass