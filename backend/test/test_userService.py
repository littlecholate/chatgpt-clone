import pytest
from unittest.mock import MagicMock
from app.db.schema.user import UserInCreate, UserInLogin, UserWithToken, UserOutput
from app.service.userService import UserService
from app.db.repository.userRepo import UserRepository
from app.core.security.hashHelper import HashHelper
from app.core.security.authHandler import AuthHandler
from fastapi import HTTPException

# Create mock objects for the dependencies
@pytest.fixture
def mock_user_repo():
    return MagicMock(spec=UserRepository)

@pytest.fixture
def mock_hash_helper(mocker):
    # We use mocker here because it's a static class, no instance is created.
    mocker.patch.object(HashHelper, 'get_password_hash')
    mocker.patch.object(HashHelper, 'verify_password')
    return HashHelper

@pytest.fixture
def mock_auth_handler(mocker):
    mocker.patch.object(AuthHandler, 'sign_jwt')
    return AuthHandler

@pytest.fixture
def user_service(mock_user_repo):
    # Pass the mock repo directly to the service
    service = UserService(session=MagicMock())
    service._UserService__userRepository = mock_user_repo # Override the private attribute
    return service

def test_signup_success(user_service, mock_user_repo, mock_hash_helper):
    """
    Tests a successful user signup.
    """
    # Set up mock behavior
    mock_user_repo.user_exist_by_email.return_value = False
    mock_hash_helper.get_password_hash.return_value = "hashed_password"
    
    # Create test data
    user_details = UserInCreate(username="new_user", email="new@example.com", password="password123")
    mock_user_repo.create_user.return_value = user_details  # Mock the return value of create_user

    # Action
    result = user_service.signup(user_details)

    # Assertions
    mock_user_repo.user_exist_by_email.assert_called_once_with(email="new@example.com")
    mock_hash_helper.get_password_hash.assert_called_once_with(plain_password="password123")
    mock_user_repo.create_user.assert_called_once()
    assert result.email == "new@example.com"

def test_signup_user_exists(user_service, mock_user_repo):
    """
    Tests signup fails when the user already exists.
    """
    # Set up mock behavior to simulate an existing user
    mock_user_repo.user_exist_by_email.return_value = True

    # Action and Assertion (expecting an HTTPException)
    with pytest.raises(HTTPException) as exc_info:
        user_details = UserInCreate(username="existing_user", email="existing@example.com", password="password123")
        user_service.signup(user_details)
    
    # Assertions on the exception
    assert exc_info.value.status_code == 400
    assert "Please Login" in exc_info.value.detail
    mock_user_repo.user_exist_by_email.assert_called_once_with(email="existing@example.com")

def test_login_success(user_service, mock_user_repo, mock_hash_helper, mock_auth_handler):
    """
    Tests a successful user login.
    """
    # Set up mock behavior
    mock_user_repo.user_exist_by_email.return_value = True
    user_output = MagicMock(id=1, email="test@example.com", password="hashed_password")
    mock_user_repo.get_user_by_email.return_value = user_output
    mock_hash_helper.verify_password.return_value = True
    mock_auth_handler.sign_jwt.return_value = "mock_jwt_token"

    # Action
    login_details = UserInLogin(email="test@example.com", password="password123")
    result = user_service.login(login_details)

    # Assertions
    mock_user_repo.user_exist_by_email.assert_called_once()
    mock_user_repo.get_user_by_email.assert_called_once_with(email="test@example.com")
    mock_hash_helper.verify_password.assert_called_once_with(plain_password="password123", hashed_password="hashed_password")
    mock_auth_handler.sign_jwt.assert_called_once_with(user_id=1)
    assert result.token == "mock_jwt_token"

def test_login_wrong_credentials(user_service, mock_user_repo, mock_hash_helper):
    """
    Tests login fails with an incorrect password.
    """
    # Set up mock behavior
    mock_user_repo.user_exist_by_email.return_value = True
    user_output = MagicMock(id=1, email="test@example.com", password="hashed_password")
    mock_user_repo.get_user_by_email.return_value = user_output
    mock_hash_helper.verify_password.return_value = False

    # Action and Assertion
    with pytest.raises(HTTPException) as exc_info:
        login_details = UserInLogin(email="test@example.com", password="wrong_password")
        user_service.login(login_details)
    
    assert exc_info.value.status_code == 400
    assert "Please check your Credentials" in exc_info.value.detail

def test_login_nonexistent_user(user_service, mock_user_repo):
    """
    Tests login fails when the user account does not exist.
    """
    # Set up mock behavior
    mock_user_repo.user_exist_by_email.return_value = False

    # Action and Assertion
    with pytest.raises(HTTPException) as exc_info:
        login_details = UserInLogin(email="nonexistent@example.com", password="password123")
        user_service.login(login_details)
    
    assert exc_info.value.status_code == 400
    assert "Please create an Account" in exc_info.value.detail

def test_get_user_by_id_success(user_service, mock_user_repo):
    """
    Tests retrieving a user by ID successfully.
    """
    # Set up mock behavior
    user_output = MagicMock(id=1, email="test@example.com")
    mock_user_repo.get_user_by_id.return_value = user_output

    # Action
    result = user_service.get_user_by_id(user_id=1)

    # Assertions
    mock_user_repo.get_user_by_id.assert_called_once_with(user_id=1)
    assert result.email == "test@example.com"

def test_get_user_by_id_not_found(user_service, mock_user_repo):
    """
    Tests for when the user ID is not found.
    """
    # Set up mock behavior
    mock_user_repo.get_user_by_id.return_value = None

    # Action and Assertion
    with pytest.raises(HTTPException) as exc_info:
        user_service.get_user_by_id(user_id=999)
    
    assert exc_info.value.status_code == 400
    assert "User is not available" in exc_info.value.detail