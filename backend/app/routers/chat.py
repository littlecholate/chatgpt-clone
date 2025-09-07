from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.service.chatService import ChatSessionService
from app.db.schema.chat import (
    ChatSessionInCreate,
    ChatSessionInUpdate,
    ChatSessionOutput,
    MessageOutput,
    MessageInCreateBody,
    MessageInUpdate,
    MessageIn,
)
chatRouter = APIRouter()
messagesRouter = APIRouter()

# Create session
@chatRouter.post("", status_code=201, response_model=ChatSessionOutput)
def create_chat_session(payload: ChatSessionInCreate, session: Session = Depends(get_db)):
    try:
        return ChatSessionService(session=session).create_session(payload=payload)
    except Exception as e:
        print(e)
        raise e

# Get single session
@chatRouter.get("/{session_id}", response_model=ChatSessionOutput)
def get_chat_session(session_id: int, session: Session = Depends(get_db)):
    try:
        return ChatSessionService(session=session).get_session(session_id=session_id)
    except Exception as e:
        print(e)
        raise e

# List sessions by user
@chatRouter.get("", response_model=List[ChatSessionOutput])
def list_chat_sessions_by_user(
    user_id: int = Query(..., description="Owner of the chat sessions"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    newest_first: bool = Query(True),
    session: Session = Depends(get_db),
):
    try:
        return ChatSessionService(session=session).list_sessions_by_user(
            user_id=user_id, limit=limit, offset=offset, newest_first=newest_first
        )
    except Exception as e:
        print(e)
        raise e

# Update (rename) session
@chatRouter.patch("/{session_id}", response_model=ChatSessionOutput)
def update_chat_session(session_id: int, payload: ChatSessionInUpdate, session: Session = Depends(get_db)):
    try:
        return ChatSessionService(session=session).update_session(session_id=session_id, payload=payload)
    except Exception as e:
        print(e)
        raise e

# Delete session
@chatRouter.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(session_id: int, session: Session = Depends(get_db)):
    try:
        ChatSessionService(session=session).delete_session(session_id=session_id)
        return
    except Exception as e:
        print(e)
        raise e

# List messages for a session
@chatRouter.get("/{session_id}/messages", response_model=List[MessageOutput])
def list_messages_for_session(
    session_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ascending: bool = Query(True),
    session: Session = Depends(get_db),
):
    try:
        return ChatSessionService(session=session).list_messages_for_session(
            session_id=session_id, limit=limit, offset=offset, ascending=ascending
        )
    except Exception as e:
        print(e)
        raise e

# Create a message inside a session
@chatRouter.post("/{session_id}/messages", status_code=201, response_model=MessageOutput)
def create_message_for_session(
    session_id: int,
    body: MessageInCreateBody,
    session: Session = Depends(get_db),
):
    try:
        return ChatSessionService(session=session).create_message(session_id=session_id, payload=body)
    except Exception as e:
        print(e)
        raise e

# Get session with eager-loaded messages
@chatRouter.get("/{session_id}/with_messages", response_model=ChatSessionOutput)
def get_session_with_messages(
    session_id: int,
    session: Session = Depends(get_db),
):
    try:
        return ChatSessionService(session=session).get_session_with_messages(session_id=session_id)
    except Exception as e:
        print(e)
        raise e

# Delete a message in a session
@chatRouter.delete("/{session_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_in_session(
    session_id: int,
    message_id: int,
    session: Session = Depends(get_db),
):
    try:
        ChatSessionService(session=session).delete_message(session_id=session_id, message_id=message_id)
        return
    except Exception as e:
        print(e)
        raise e

@chatRouter.post("/{session_id}/messages/stream")
def post_message_stream(session_id: int, body: MessageIn, session: Session = Depends(get_db)):
    text = (body.content or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="content is empty")

    generator = ChatSessionService(session=session).stream_user_and_robot_message(session_id=session_id, user_text=text, mode=body.mode)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",  # adjust for production
        },
    )

@messagesRouter.put("/{message_id}", response_model=MessageOutput)
def update_message(
    message_id: int,
    payload: MessageInUpdate,
    session: Session = Depends(get_db),
):
    try:
        return ChatSessionService(session=session).update_message(message_id=message_id, payload=payload)
    except Exception as e:
        print(e)
        raise e
