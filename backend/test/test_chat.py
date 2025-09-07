import pytest
from app.db.schema.chat import ChatSessionInCreate, MessageInCreateBody
from app.db.schema.user import UserInCreate
from app.core.security.hashHelper import HashHelper
from app.db.repository.userRepo import UserRepository
from main import app

# A helper fixture to create a user and get a token
@pytest.fixture
def test_user(db_session):
    """
    Creates and returns a test user, and logs them in to get an auth token.
    This can be used for protected routes.
    """
    user_repo = UserRepository(session=db_session)
    user_data = UserInCreate(
        username="testchatuser",
        email="chatuser@example.com",
        password=HashHelper.get_password_hash("testpassword")
    )
    user = user_repo.create_user(user_data)
    # Note: Your current auth flow returns a token from /login,
    # so we'd need to mock the login or get the token directly if possible.
    # For now, we'll assume a way to get the token is available or test unauthenticated routes.
    # We will skip protected routes until the auth token is managed in test setup.
    return user

def test_create_chat_session(client):
    """
    Tests creating a new chat session.
    """
    payload = {"user_id": 1, "name": "Test Session"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["user_id"] == 1
    assert data["name"] == "Test Session"

def test_get_chat_session(client):
    """
    Tests getting a single chat session by ID.
    """
    # First, create a session to retrieve
    payload = {"user_id": 1, "name": "Session for GET"}
    create_res = client.post("/chat", json=payload)
    session_id = create_res.json()["id"]

    # Now, get the session
    response = client.get(f"/chat/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["name"] == "Session for GET"

def test_get_nonexistent_chat_session(client):
    """
    Tests getting a chat session that does not exist.
    """
    response = client.get("/chat/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Chat session not found"

def test_list_sessions_by_user(client):
    """
    Tests listing chat sessions for a specific user.
    """
    user_id = 2
    # Create multiple sessions for the user
    client.post("/chat", json={"user_id": user_id, "name": "Session A"})
    client.post("/chat", json={"user_id": user_id, "name": "Session B"})

    response = client.get(f"/chat?user_id={user_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Session B" # Newest first is default

def test_update_chat_session(client):
    """
    Tests renaming a chat session.
    """
    # Create a session first
    create_res = client.post("/chat", json={"user_id": 3, "name": "Old Name"})
    session_id = create_res.json()["id"]

    # Update the name
    payload = {"name": "New Name"}
    response = client.patch(f"/chat/{session_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"

def test_delete_chat_session(client):
    """
    Tests deleting a chat session.
    """
    # Create a session
    create_res = client.post("/chat", json={"user_id": 4, "name": "To Be Deleted"})
    session_id = create_res.json()["id"]

    # Delete the session
    response = client.delete(f"/chat/{session_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_res = client.get(f"/chat/{session_id}")
    assert get_res.status_code == 404

def test_create_message_in_session(client):
    """
    Tests creating a new message inside a chat session.
    """
    # Create a session first
    create_res = client.post("/chat", json={"user_id": 5, "name": "Message Test Session"})
    session_id = create_res.json()["id"]

    # Create a message
    payload = {"role": "user", "content": "Hello, world!"}
    response = client.post(f"/chat/{session_id}/messages", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["session_id"] == session_id
    assert data["role"] == "user"
    assert data["content"] == "Hello, world!"