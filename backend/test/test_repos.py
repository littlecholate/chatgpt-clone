from app.db.repository.userRepo import UserRepository
from app.db.schema.user import UserInCreate
from app.db.models.user import User
from app.db.repository.chatRepo import ChatSessionRepository, MessageRepository
from app.db.schema.chat import ChatSessionInCreate, MessageInCreate
import pytest

def test_create_user(db_session):
    """
    Tests the create_user method in the UserRepository.
    """
    user_repo = UserRepository(session=db_session)
    user_data = UserInCreate(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    # Action
    new_user = user_repo.create_user(user_data=user_data)
    
    # Assertions
    assert new_user is not None
    assert new_user.email == "test@example.com"
    assert db_session.query(User).filter_by(email="test@example.com").first() is not None

def test_user_exist_by_email_true(db_session):
    """
    Tests user_exist_by_email when the user exists.
    """
    user_repo = UserRepository(session=db_session)
    # Arrange: create a user first
    user_data = UserInCreate(
        username="existing",
        email="existing@example.com",
        password="password"
    )
    user_repo.create_user(user_data=user_data)

    # Action & Assertion
    assert user_repo.user_exist_by_email("existing@example.com") is True

def test_user_exist_by_email_false(db_session):
    """
    Tests user_exist_by_email when the user does not exist.
    """
    user_repo = UserRepository(session=db_session)
    assert user_repo.user_exist_by_email("nonexistent@example.com") is False

def test_create_message_success_with_auto_title(db_session):
    """
    Tests creating the first message in a session and verifies auto-titling.
    """
    # Arrange
    user_id = 1
    # Create a session with the default name
    session_repo = ChatSessionRepository(session=db_session)
    payload = ChatSessionInCreate(user_id=user_id, name="New Chat")
    chat_session = session_repo.create_session(data=payload)

    msg_repo = MessageRepository(session=db_session)
    
    # Action
    payload = MessageInCreate(session_id=chat_session.id, role="user", content="Test message content")
    new_message = msg_repo.create_message(data=payload)
    
    # Assertions
    assert new_message is not None
    assert new_message.content == "Test message content"
    assert new_message.session_id == chat_session.id
    
    # Verify the session name was updated
    updated_session = session_repo.get_session_by_id(chat_session.id)
    assert updated_session.name == "Test messa" # SNIPPET_LEN is 10

def test_create_message_without_auto_title(db_session):
    """
    Tests creating a message in an existing session (no auto-titling).
    """
    # Arrange
    user_id = 1
    session_repo = ChatSessionRepository(session=db_session)
    
    # Initialize the session with a name that is NOT the default "New Chat"
    payload = ChatSessionInCreate(user_id=user_id, name="My Initial Chat") 
    chat_session = session_repo.create_session(data=payload)

    msg_repo = MessageRepository(session=db_session)
    
    # Create an initial message
    payload_1 = MessageInCreate(session_id=chat_session.id, role="user", content="First message")
    msg_repo.create_message(data=payload_1)
    
    # Action: Create a second message
    payload_2 = MessageInCreate(session_id=chat_session.id, role="user", content="Second message")
    second_message = msg_repo.create_message(data=payload_2)
    
    # Assertions
    assert second_message.content == "Second message"
    
    # Verify the session name was NOT updated
    updated_session = session_repo.get_session_by_id(chat_session.id)
    assert updated_session.name == "My Initial Chat"

def test_get_message_by_id_success(db_session):
    """
    Tests retrieving a message by a valid ID.
    """
    # Create a session first to get its ID
    session_repo = ChatSessionRepository(session=db_session)
    chat_session = session_repo.create_session(data=ChatSessionInCreate(user_id=1, name="Test Session"))

    # Arrange
    msg_repo = MessageRepository(session=db_session)
    # A dummy message to retrieve
    new_message = msg_repo.create_message(data=MessageInCreate(session_id=chat_session.id, role="user", content="Hello"))
    
    # Action
    retrieved_message = msg_repo.get_message_by_id(new_message.id)
    
    # Assertions
    assert retrieved_message is not None
    assert retrieved_message.id == new_message.id

def test_get_message_by_id_not_found(db_session):
    """
    Tests retrieving a message with a non-existent ID.
    """
    msg_repo = MessageRepository(session=db_session)
    retrieved_message = msg_repo.get_message_by_id(999)
    assert retrieved_message is None

def test_delete_message_success(db_session):
    """
    Tests successful deletion of a message.
    """
    # Arrange
    # First, create a chat session to get a valid session_id
    from app.db.schema.chat import ChatSessionInCreate
    from app.db.repository.chatRepo import ChatSessionRepository
    
    session_repo = ChatSessionRepository(session=db_session)
    chat_session_payload = ChatSessionInCreate(user_id=1, name="Session for Deletion")
    chat_session = session_repo.create_session(data=chat_session_payload)
    
    msg_repo = MessageRepository(session=db_session)
    
    # Now use the new chat session's ID to create the message
    message_payload = MessageInCreate(session_id=chat_session.id, role="user", content="Delete me")
    message_to_delete = msg_repo.create_message(data=message_payload)

    # Action
    is_deleted = msg_repo.delete_message(message_to_delete.id)
    
    # Assertions
    assert is_deleted is True
    assert msg_repo.get_message_by_id(message_to_delete.id) is None

def test_delete_message_not_found(db_session):
    """
    Tests deletion fails for a non-existent message.
    """
    msg_repo = MessageRepository(session=db_session)
    is_deleted = msg_repo.delete_message(999)
    assert is_deleted is False

def test_list_messages_by_session_sorting_and_pagination(db_session):
    """
    Tests listing messages with ascending/descending order, limit, and offset.
    """
    # Arrange: Create a session and multiple messages
    user_id = 1
    session_repo = ChatSessionRepository(session=db_session)
    payload = ChatSessionInCreate(user_id=user_id, name="New Chat")
    chat_session = session_repo.create_session(data=payload)
    msg_repo = MessageRepository(session=db_session)
    
    for i in range(5):
        msg_repo.create_message(data=MessageInCreate(session_id=chat_session.id, role="user", content=f"Message {i}"))
        
    # Action 1: List with default (ascending) order
    messages_asc = msg_repo.list_messages_by_session(session_id=chat_session.id)
    assert len(messages_asc) == 5
    assert messages_asc[0].content == "Message 0"
    
    # Action 2: List with descending order
    messages_desc = msg_repo.list_messages_by_session(session_id=chat_session.id, ascending=False)
    assert messages_desc[0].content == "Message 4"
    
    # Action 3: List with limit and offset
    messages_paged = msg_repo.list_messages_by_session(session_id=chat_session.id, limit=2, offset=1)
    assert len(messages_paged) == 2
    assert messages_paged[0].content == "Message 1"
    
def test_get_last_message(db_session):
    """
    Tests retrieving the last message in a session.
    """
    # Arrange
    # Create a chat session first to get a valid session_id
    from app.db.repository.chatRepo import ChatSessionRepository
    from app.db.schema.chat import ChatSessionInCreate, MessageInCreate

    session_repo = ChatSessionRepository(session=db_session)
    chat_session = session_repo.create_session(
        data=ChatSessionInCreate(user_id=1, name="Test Session")
    )
    
    msg_repo = MessageRepository(session=db_session)
    
    # Create multiple messages using the ID of the new session
    msg_repo.create_message(data=MessageInCreate(session_id=chat_session.id, role="user", content="First"))
    msg_repo.create_message(data=MessageInCreate(session_id=chat_session.id, role="user", content="Second"))
    
    # Action
    last_message = msg_repo.get_last_message(chat_session.id)
    
    # Assertions
    assert last_message is not None
    assert last_message.content == "Second"

def test_update_message_success(db_session):
    """
    Tests updating a message's role and content.
    """
    # Arrange
    # First, create a chat session to get a valid session_id
    from app.db.schema.chat import ChatSessionInCreate, MessageInCreate
    from app.db.repository.chatRepo import ChatSessionRepository
    
    session_repo = ChatSessionRepository(session=db_session)
    chat_session_payload = ChatSessionInCreate(user_id=1, name="Session for Update")
    chat_session = session_repo.create_session(data=chat_session_payload)
    
    msg_repo = MessageRepository(session=db_session)
    
    # Now use the new chat session's ID to create the message
    message_payload = MessageInCreate(session_id=chat_session.id, role="user", content="Original content")
    message_to_update = msg_repo.create_message(data=message_payload)

    # Action
    updated_message = msg_repo.update_message(
        message_id=message_to_update.id,
        role="robot",
        content="Updated content"
    )
    
    # Assertions
    assert updated_message is not None
    assert updated_message.role == "robot"
    assert updated_message.content == "Updated content"

def test_update_message_partial_update(db_session):
    """
    Tests updating only one field (e.g., content).
    """
    # Arrange
    # Create a chat session first to get a valid session_id
    from app.db.schema.chat import ChatSessionInCreate, MessageInCreate
    from app.db.repository.chatRepo import ChatSessionRepository
    
    session_repo = ChatSessionRepository(session=db_session)
    chat_session_payload = ChatSessionInCreate(user_id=1, name="Session for Partial Update")
    chat_session = session_repo.create_session(data=chat_session_payload)
    
    msg_repo = MessageRepository(session=db_session)
    
    # Now use the new chat session's ID to create the message
    message_payload = MessageInCreate(session_id=chat_session.id, role="user", content="Old content")
    message_to_update = msg_repo.create_message(data=message_payload)

    # Action: Only update content
    updated_message = msg_repo.update_message(
        message_id=message_to_update.id,
        content="New content"
    )
    
    # Assertions
    assert updated_message is not None
    assert updated_message.role == "user"
    assert updated_message.content == "New content"
    
def test_update_message_not_found(db_session):
    """
    Tests updating a message that does not exist.
    """
    msg_repo = MessageRepository(session=db_session)
    updated_message = msg_repo.update_message(message_id=999, content="No message here")
    assert updated_message is None

def test_update_message_no_payload(db_session):
    """
    Tests that a message is not updated if no payload is provided.
    """
    # Arrange
    # Create a chat session first to get a valid session_id
    from app.db.schema.chat import ChatSessionInCreate, MessageInCreate
    from app.db.repository.chatRepo import ChatSessionRepository
    
    session_repo = ChatSessionRepository(session=db_session)
    chat_session_payload = ChatSessionInCreate(user_id=1, name="Session with No Payload Update")
    chat_session = session_repo.create_session(data=chat_session_payload)
    
    msg_repo = MessageRepository(session=db_session)
    
    # Now use the new chat session's ID to create the message
    message_payload = MessageInCreate(session_id=chat_session.id, role="user", content="No update")
    message_to_update = msg_repo.create_message(data=message_payload)
    
    # Action: Call update without any role or content
    updated_message = msg_repo.update_message(message_id=message_to_update.id, role=None, content=None)
    
    # Assertions
    assert updated_message.content == "No update"
    assert updated_message.role == "user"