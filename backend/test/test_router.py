import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Assumes a client fixture is defined in conftest.py that uses
# the FastAPI TestClient with a mocked database.

# --- Test authRouter ---
# These tests cover user registration and login functionality.

def test_signup_success(client: TestClient):
    """Tests a successful user signup."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword"
    }
    response = client.post("/auth/signup", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "username" in data
    assert data["email"] == "test@example.com"
    assert "password" not in data
    
def test_signup_user_already_exists(client: TestClient):
    """Tests that a user cannot sign up with an existing email."""
    payload = {
        "username": "existing_user",
        "email": "exists@example.com",
        "password": "password"
    }
    client.post("/auth/signup", json=payload)
    response = client.post("/auth/signup", json=payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Please Login"
    
def test_login_success(client: TestClient):
    """Tests a successful user login."""
    signup_payload = {
        "username": "login_user",
        "email": "login@example.com",
        "password": "password123"
    }
    client.post("/auth/signup", json=signup_payload)
    
    login_payload = {
        "email": "login@example.com",
        "password": "password123"
    }
    response = client.post("/auth/login", json=login_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert len(data["token"]) > 0
    
def test_login_wrong_credentials(client: TestClient):
    """Tests that login fails with incorrect credentials."""
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Please create an Account"

# --- Test chatRouter ---
# These tests cover CRUD for chat sessions.

def test_create_chat_session_success(client: TestClient):
    """Tests creating a chat session for a user."""
    payload = {"user_id": 1, "name": "New Chat"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["user_id"] == 1
    assert data["name"] == "New Chat"

def test_get_chat_session_success(client: TestClient):
    """Tests retrieving a specific chat session."""
    create_payload = {"user_id": 1, "name": "Session to Get"}
    create_response = client.post("/chat", json=create_payload)
    session_id = create_response.json()["id"]
    
    response = client.get(f"/chat/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["name"] == "Session to Get"

def test_list_sessions_by_user_success(client: TestClient):
    """Tests listing chat sessions for a specific user."""
    user_id = 2
    client.post("/chat", json={"user_id": user_id, "name": "Chat A"})
    client.post("/chat", json={"user_id": user_id, "name": "Chat B"})
    
    response = client.get(f"/chat?user_id={user_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Chat B"

def test_update_chat_session_success(client: TestClient):
    """Tests updating the name of a chat session."""
    create_response = client.post("/chat", json={"user_id": 3, "name": "Old Name"})
    session_id = create_response.json()["id"]
    
    update_payload = {"name": "New Name"}
    response = client.patch(f"/chat/{session_id}", json=update_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"

def test_delete_chat_session_success(client: TestClient):
    """Tests deleting a chat session."""
    create_response = client.post("/chat", json={"user_id": 4, "name": "To Be Deleted"})
    session_id = create_response.json()["id"]
    
    response = client.delete(f"/chat/{session_id}")
    
    assert response.status_code == 204
    
    get_response = client.get(f"/chat/{session_id}")
    assert get_response.status_code == 404

# --- New tests for chatRouter and messagesRouter ---

def test_list_messages_for_session_success(client: TestClient):
    """
    Tests listing messages for a specific chat session.
    """
    user_id = 10
    session_id = client.post("/chat", json={"user_id": user_id, "name": "Message List Session"}).json()["id"]
    client.post(f"/chat/{session_id}/messages", json={"role": "user", "content": "Msg 1"})
    client.post(f"/chat/{session_id}/messages", json={"role": "user", "content": "Msg 2"})

    response = client.get(f"/chat/{session_id}/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Msg 1"

def test_create_message_for_session_success(client: TestClient):
    """
    Tests creating a new message inside a chat session.
    """
    create_response = client.post("/chat", json={"user_id": 5, "name": "Message Test Session"})
    session_id = create_response.json()["id"]
    
    message_payload = {"role": "user", "content": "Hello, world!"}
    response = client.post(f"/chat/{session_id}/messages", json=message_payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["session_id"] == session_id
    assert data["content"] == "Hello, world!"
    
def test_get_session_with_messages_success(client: TestClient):
    """
    Tests retrieving a chat session with its messages eagerly loaded.
    """
    user_id = 20
    session_id = client.post("/chat", json={"user_id": user_id, "name": "Session with Messages"}).json()["id"]
    client.post(f"/chat/{session_id}/messages", json={"role": "user", "content": "Hello"})
    client.post(f"/chat/{session_id}/messages", json={"role": "robot", "content": "Hi there"})
    
    response = client.get(f"/chat/{session_id}/with_messages")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hello"

def test_delete_message_in_session_success(client: TestClient):
    """
    Tests deleting a message within a session.
    """
    user_id = 30
    session_id = client.post("/chat", json={"user_id": user_id, "name": "Session with Deletable Message"}).json()["id"]
    message_id = client.post(f"/chat/{session_id}/messages", json={"role": "user", "content": "Delete me"}).json()["id"]
    
    response = client.delete(f"/chat/{session_id}/messages/{message_id}")
    
    assert response.status_code == 204
    
    # Verify the message is gone
    get_response = client.get(f"/chat/{session_id}/messages")
    assert len(get_response.json()) == 0

def test_update_message_success(client: TestClient):
    """
    Tests updating a message's content via the messagesRouter PUT endpoint.
    """
    user_id = 40
    session_id = client.post("/chat", json={"user_id": user_id, "name": "Session to Update Message"}).json()["id"]
    message_id = client.post(f"/chat/{session_id}/messages", json={"role": "user", "content": "Old content"}).json()["id"]
    
    update_payload = {"role": "robot", "content": "New content"}
    response = client.put(f"/messages/{message_id}", json=update_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "New content"
    assert data["role"] == "robot"
    
def test_stream_message_success(client: TestClient, mocker):
    """
    Tests the streaming message endpoint.
    """
    user_id = 50
    session_id = client.post("/chat", json={"user_id": user_id, "name": "Streaming Test Session"}).json()["id"]
    
    # Mock the service method that handles the streaming
    mocked_generator = MagicMock()
    mocked_generator.return_value = (
        "data: Hello\n\n",
        "data: world!\n\n",
        "event:done\ndata:ok\n\n",
    )
    mocker.patch('app.service.chatService.ChatSessionService.stream_user_and_robot_message', return_value=mocked_generator.return_value)
    
    payload = {"content": "Test stream", "mode": 1}
    response = client.post(f"/chat/{session_id}/messages/stream", json=payload)
    
    assert response.status_code == 200
    # Change the assertion to check if the expected content type is a substring
    assert "text/event-stream" in response.headers["content-type"]
    
    # Verify the content of the streamed response
    streamed_data = response.content.decode('utf-8')
    assert "data: Hello\n\n" in streamed_data
    assert "data: world!\n\n" in streamed_data
    assert "event:done\ndata:ok\n\n" in streamed_data