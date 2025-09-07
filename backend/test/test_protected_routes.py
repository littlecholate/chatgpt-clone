import pytest
import time
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from app.util.protectRoute import get_current_user
from app.db.schema.user import UserOutput
from app.core.security.authHandler import AuthHandler
from app.service.userService import UserService

# Fixture to override the get_db dependency
@pytest.fixture
def mock_get_db_override():
    mock_session = MagicMock()
    return mock_session

# Fixture to override the get_current_user dependency
@pytest.fixture
def override_get_current_user_fixture(mock_get_db_override):
    def override_get_current_user_mock():
        return UserOutput(id=1, username="testuser", email="test@example.com")
    
    # Use app.dependency_overrides to replace the real dependency
    app.dependency_overrides[get_current_user] = override_get_current_user_mock
    yield
    app.dependency_overrides.clear() # Clean up after the test

def test_protected_route_with_valid_token(client, override_get_current_user_fixture):
    """
    Tests a protected route with a valid token by overriding the dependency.
    """
    response = client.get("/protected", headers={"Authorization": "Bearer some_token"})
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"
    
def test_protected_route_without_token(client):
    """
    Tests a protected route without a token.
    """
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Authentication Credentials"

def test_protected_route_with_malformed_token(client, mocker):
    """
    Tests a protected route with a malformed Authorization header.
    """
    # Mock the decode_jwt method to return None, simulating a bad token
    mocker.patch.object(AuthHandler, 'decode_jwt', return_value=None)
    
    response = client.get("/protected", headers={"Authorization": "Invalid Token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Authentication Credentials"

def test_protected_route_with_invalid_user_id(client, mocker):
    """
    Tests a protected route when the user ID from the token is not found.
    """
    # Mock the decode_jwt method to return a valid payload
    mocker.patch.object(AuthHandler, 'decode_jwt', return_value={"user_id": 999, "expires": time.time() + 90000})
    # Mock the get_user_by_id service method to raise an error
    mocker.patch.object(UserService, 'get_user_by_id', side_effect=Exception("User not found"))
    
    response = client.get("/protected", headers={"Authorization": "Bearer token_with_invalid_id"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Authentication Credentials"