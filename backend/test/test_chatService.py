import pytest
import requests_mock
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.service.chatService import ChatSessionService
from app.db.schema.chat import (
    ChatSessionInCreate,
    ChatSessionInUpdate,
    MessageInCreate,
    MessageInCreateBody,
    MessageOutput,
)
from app.db.schema.chat import MessageInUpdate
from app.db.models.chat import ChatSession, Message
from app.service import chatService

# This fixture provides a mocked ChatSessionService for testing
@pytest.fixture
def chat_service(mocker):
    # Mock the repository classes themselves
    mocker.patch('app.db.repository.chatRepo.ChatSessionRepository')
    mocker.patch('app.db.repository.chatRepo.MessageRepository')
    
    # Create the service instance
    service = ChatSessionService(session=MagicMock())
    
    # Return the service instance with its mocked dependencies
    return service

def test_create_session(chat_service, mocker):
    """
    Tests successful creation of a chat session.
    """
    # Mock the repository's create_session method to return a mock object
    mock_session = MagicMock(spec=ChatSession)
    mocker.patch.object(chat_service._sessions, 'create_session', return_value=mock_session)
    
    payload = ChatSessionInCreate(user_id=1, name="Test Session")
    created_session = chat_service.create_session(payload)
    
    chat_service._sessions.create_session.assert_called_once_with(data=payload)
    assert created_session is mock_session
    
def test_get_session_not_found(chat_service, mocker):
    """
    Tests that get_session raises 404 for a non-existent session.
    """
    mocker.patch.object(chat_service._sessions, 'get_session_by_id', return_value=None)
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.get_session(session_id=999)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

def test_update_session_not_found(chat_service, mocker):
    """
    Tests that update_session raises 404 for a non-existent session.
    """
    mocker.patch.object(chat_service._sessions, 'get_session_by_id', return_value=None)
    payload = ChatSessionInUpdate(name="New Name")
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.update_session(session_id=999, payload=payload)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

def test_update_session_with_empty_payload(chat_service, mocker):
    """
    Tests that update_session does nothing if the payload has no name.
    """
    mock_session = MagicMock(spec=ChatSession)
    
    # Mock the get_session_by_id method
    mocker.patch.object(chat_service._sessions, 'get_session_by_id', return_value=mock_session)
    
    # Explicitly mock the rename_session method so we can assert on it later
    mock_rename_session = mocker.patch.object(chat_service._sessions, 'rename_session')
    
    payload = ChatSessionInUpdate(name=None)
    
    updated_session = chat_service.update_session(session_id=1, payload=payload)
    
    assert updated_session is mock_session
    
    # Now that the method is mocked, this assertion will work
    mock_rename_session.assert_not_called()

def test_delete_session_not_found(chat_service, mocker):
    """
    Tests that delete_session raises 404 for a non-existent session.
    """
    mocker.patch.object(chat_service._sessions, 'delete_session', return_value=False)
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.delete_session(session_id=999)
        
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

def test_create_message_not_found(chat_service, mocker):
    """
    Tests that create_message raises 404 for a non-existent session.
    """
    mocker.patch.object(chat_service._sessions, 'session_exists', return_value=False)
    payload = MagicMock()
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.create_message(session_id=999, payload=payload)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

def test_list_messages_for_session_not_found(chat_service, mocker):
    """
    Tests that list_messages_for_session raises 404 for a non-existent session.
    """
    mocker.patch.object(chat_service._sessions, 'session_exists', return_value=False)
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.list_messages_for_session(session_id=999)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

def test_delete_message_not_found_in_session(chat_service, mocker):
    """
    Tests that delete_message raises 404 if the message is not found or
    does not belong to the session.
    """
    # Mock dependencies
    mocker.patch.object(chat_service._sessions, 'session_exists', return_value=True)
    mocker.patch.object(chat_service._messages, 'get_message_by_id', return_value=None)
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.delete_message(session_id=1, message_id=999)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Message not found in this session"

def test_update_message_no_payload(chat_service, mocker):
    """
    Tests that update_message raises 400 when no payload is provided.
    """
    # Use MessageInUpdate instead of ChatSessionInUpdate
    payload = MessageInUpdate(role=None, content=None)
    
    with pytest.raises(HTTPException) as exc_info:
        chat_service.update_message(message_id=1, payload=payload)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Nothing to update"

def test_get_session_with_messages_not_found(chat_service, mocker):
    """
    Tests that get_session_with_messages raises 404 for a non-existent session.
    """
    # Create a mock for the entire query chain
    mock_query = mocker.MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None  # The final method returns None

    # Patch the initial `query` method to return our mocked query chain
    mocker.patch.object(chat_service._sessions.session, 'query', return_value=mock_query)

    with pytest.raises(HTTPException) as exc_info:
        chat_service.get_session_with_messages(session_id=999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

# --- Tests for Stream Methods ---
        
def test_stream_mode_2_web_search(chat_service, mocker):
    """
    Tests that web search is correctly triggered and the results are added to the history.
    """
    user_text = "What's the weather in Tokyo?"
    web_results = "The weather in Tokyo is sunny."

    # Mock dependencies
    mocker.patch.object(chat_service._sessions, 'session_exists', return_value=True)
    mocker.patch.object(chat_service._messages, 'list_messages_by_session', return_value=[])
    
    # Patch the function at the module level where it is used
    mocked_web_search = mocker.patch('app.service.chatService.web_search_summary', return_value=web_results)

    # Mock httpx.stream
    with requests_mock.Mocker() as m:
        m.post("http://localhost:8000/v1/chat/completions", text="data: [DONE]\n\n")

        # Action
        list(chat_service.stream_user_and_robot_message(session_id=1, user_text=user_text, mode=2))

    # Assertions
    # Use the mocked object returned by mocker.patch
    mocked_web_search.assert_called_once_with(user_text, max_results=5)

def test_stream_mode_3_rag(chat_service, mocker):
    """
    Tests that RAG is correctly triggered and the results are added to the history.
    """
    user_text = "How to write a good poem?"
    rag_docs = ["File: poem_guide.pdf - A guide to poetry.", "File: sonnets.docx - Examples of sonnets."]

    # Mock dependencies
    mocker.patch.object(chat_service._sessions, 'session_exists', return_value=True)
    mocker.patch.object(chat_service._messages, 'list_messages_by_session', return_value=[])
    
    # Patch the function at the module level where it is used
    mocked_query_rag_db = mocker.patch('app.service.chatService.query_rag_db', return_value=rag_docs)

    # Mock httpx.stream
    with requests_mock.Mocker() as m:
        m.post("http://localhost:8000/v1/chat/completions", text="data: [DONE]\n\n")

        # Action
        list(chat_service.stream_user_and_robot_message(session_id=1, user_text=user_text, mode=3))

    # Assertions
    mocked_query_rag_db.assert_called_once_with(user_text, k=4)