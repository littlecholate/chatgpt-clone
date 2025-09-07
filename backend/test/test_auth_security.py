import pytest
import jwt
import time
from unittest.mock import patch
from app.core.security.authHandler import AuthHandler

# Mock the environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch('app.core.security.authHandler.config') as mock_config:
        mock_config.return_value = "TEST_SECRET"
        yield

def test_sign_jwt_success():
    """
    Tests that a JWT token is correctly signed and encoded.
    """
    user_id = 123
    token = AuthHandler.sign_jwt(user_id)
    
    # Assert the token is a string
    assert isinstance(token, str)
    
    # Manually decode the token to verify the payload
    decoded_payload = jwt.decode(token, "TEST_SECRET", algorithms=["HS256"], options={"verify_signature": False})
    
    assert "user_id" in decoded_payload
    assert "expires" in decoded_payload
    assert decoded_payload["user_id"] == user_id
    # Assert that the expiration time is in the future
    assert decoded_payload["expires"] > time.time()

def test_decode_jwt_expired_token():
    """
    Tests decoding an expired JWT token.
    """
    # Create a token with an expiration time in the past
    expired_payload = {"user_id": 123, "expires": time.time() - 90000}
    expired_token = jwt.encode(expired_payload, "TEST_SECRET", algorithm="HS256")
    
    decoded_payload = AuthHandler.decode_jwt(expired_token)
    
    assert decoded_payload is None

def test_decode_jwt_invalid_token():
    """
    Tests decoding a token with an invalid secret.
    """
    # Create a token with a different secret
    invalid_token = jwt.encode({"user_id": 123, "expires": time.time() + 90000}, "WRONG_SECRET", algorithm="HS256")
    
    # The decode_jwt method will return None in this case due to the try-except block
    decoded_payload = AuthHandler.decode_jwt(invalid_token)
    
    assert decoded_payload is None