from typing import Generator, List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from contextlib import suppress
import httpx
import os, json

from app.tools.web_search import web_search_summary 
# Imports for tool-calling
from app.tools.llm_tool import WEB_SEARCH_TOOL, run_tool_call, ToolCallBuffer
from app.chroma_rag import query_rag_db

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
        self, session_id: int, user_text: str, mode: int,
    ) -> Generator[str, None, None]:
        """
        - Save user msg
        - Call robot endpoint with history + user input
        - Yield tokens as SSE
        - Save final robot msg
        """
        # Get the current frontend mode
        # mode 1 = think, mode 2 = web_search, mode 3 = RAG

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
                    "Almost generate at lease 30 words but at more 200 words"
                    "If web results are provided below, prefer them for facts and cite links in markdown. "
                    "If LOCAL FILE CONTEXT is provided, ground your answer in it and quote file names when relevant."
                ),
            }
        ]
        """Convert DB messages to [{role, content}, ...]."""
        msgs = self._messages.list_messages_by_session(
            session_id=session_id, limit=100, offset=0, ascending=True
        )
        history.extend([{"role": m.role, "content": m.content} for m in msgs])

        # 2a) (NEW) Web search pre-hook (heuristic or force)
        do_search = True if mode == 2 else False
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

        # RAG pre-hook (heuristic or force)
        do_rag = True if mode == 3 else False
        if do_rag:
            rag_docs = query_rag_db(user_text, k=4)
            if rag_docs:
                rag_context = "\n\n".join(rag_docs)
                history.append({
                    "role": "system",
                    "content": (
                        "LOCAL FILE CONTEXT (use if relevant and cite the filename):\n\n"
                        f"{rag_context}"
                    ),
                })

        # 3. Prepare request payload
        enable_thinking = True if mode == 1 else False
        payload = {
            "model": ROBOT_MODEL,
            "messages": history,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
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

    def stream_user_and_robot_message__(   # <- new method name for tool-calling
        self,
        session_id: int,
        user_text: str,
        mode: int,
    ) -> Generator[str, None, None]:
        """
        - Save user msg
        - Register web_search tool
        - Stream assistant; if tool_call appears, execute locally, append role='tool' message, resume
        - Yield tokens as SSE
        - Save final assistant msg
        """

        # 1) Save user message
        if not self._sessions.session_exists(session_id=session_id):
            raise HTTPException(status_code=404, detail="Chat session not found")
        msg_in = MessageInCreate(session_id=session_id, role="user", content=user_text)
        self._messages.create_message(data=msg_in)

        # 2) Build history (system + prior messages)
        history = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Do not reveal hidden reasoning. "
                    "You can call tools to get up-to-date or factual info. "
                    "If you use web_search, cite links in markdown."
                ),
            }
        ]
        msgs = self._messages.list_messages_by_session(
            session_id=session_id, limit=100, offset=0, ascending=True
        )
        history.extend([{"role": m.role, "content": m.content} for m in msgs])

        # 3) Prepare initial payload with tool schema
        payload = {
            "model": ROBOT_MODEL,
            "messages": history,
            "tools": [WEB_SEARCH_TOOL],
            "tool_choice": "auto",
            "stream": True,
        }

        pieces: List[str] = []
        tool_buf = ToolCallBuffer()

        def _stream_once(req_payload) -> bool:
            """
            Stream once from the model.
            Returns True if at least one tool_call was executed (meaning we should re-invoke);
            Returns False when no further tool calls occurred (final answer likely done).
            """
            nonlocal pieces, history, tool_buf

            tool_used_this_turn = False

            with httpx.stream("POST", ROBOT_ENDPOINT, json=req_payload, timeout=None) as r:
                for line in r.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[len("data: "):]
                    if data.strip() == "[DONE]":
                        break

                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"]

                    # Tool-calling branch: accumulate chunks until complete
                    if "tool_calls" in delta:
                        for d in delta["tool_calls"]:
                            complete = tool_buf.add_delta(d)
                            if complete:
                                # append the assistant's tool_calls message (required by spec)
                                history.append({"role": "assistant", "tool_calls": [complete]})
                                # run the tool locally
                                tool_msg = run_tool_call(complete)
                                history.append(tool_msg)
                                tool_used_this_turn = True
                        # don't emit text for tool meta
                        continue

                    # Normal text delta
                    content_piece = delta.get("content")
                    if content_piece:
                        pieces.append(content_piece)
                        yield f"data:{content_piece}\n\n"

            return tool_used_this_turn

        try:
            # 4) Loop: stream → maybe tool → resume
            hops = 0
            need_resume = _stream_once(payload)
            max_tool_hops = 3 # prevent infinite loops
            while need_resume and hops < max_tool_hops:
                hops += 1
                # after tools are appended to history, resume WITHOUT the tools schema
                # (optional: you can include tools again if you expect chaining)
                follow = {
                    "model": ROBOT_MODEL,
                    "messages": history,
                    "stream": True,
                }
                need_resume = _stream_once(follow)

            final_text = "".join(pieces).strip()

            # 5) Save assistant message
            msg_in = MessageInCreate(session_id=session_id, role="robot", content=final_text)
            self._messages.create_message(data=msg_in)

            yield "event:done\ndata:ok\n\n"

        finally:
            with suppress(Exception):
                pass