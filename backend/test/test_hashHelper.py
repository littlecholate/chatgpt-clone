import pytest
from app.core.security.hashHelper import HashHelper

def test_get_password_hash():
    """
    Tests that a password hash is correctly generated.
    """
    # Arrange
    plain_password = "mysecretpassword"

    # Action
    hashed_password = HashHelper.get_password_hash(plain_password)

    # Assertions
    # The hash should be a string
    assert isinstance(hashed_password, str)
    # The hash should not be the same as the plain password
    assert hashed_password != plain_password
    # The hash should be verifiable
    assert HashHelper.verify_password(plain_password, hashed_password)

def test_verify_password_success():
    """
    Tests that a correct password is successfully verified.
    """
    # Arrange
    plain_password = "mysecretpassword"
    # Create a real hash to test against
    hashed_password = HashHelper.get_password_hash(plain_password)

    # Action
    is_valid = HashHelper.verify_password(plain_password, hashed_password)

    # Assertions
    assert is_valid is True

def test_verify_password_failure():
    """
    Tests that a wrong password is not verified.
    """
    # Arrange
    correct_password = "mysecretpassword"
    wrong_password = "notthepassword"
    # Create a real hash for the correct password
    hashed_password = HashHelper.get_password_hash(correct_password)

    # Action
    is_valid = HashHelper.verify_password(wrong_password, hashed_password)

    # Assertions
    assert is_valid is False