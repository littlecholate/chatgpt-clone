import pytest
from unittest.mock import MagicMock
from app.core.database import get_db, SessionLocal

def test_get_db_yields_session_and_closes(mocker):
    """
    Tests that get_db yields a session and ensures db.close() is called.
    """
    # Arrange: Mock the SessionLocal class to return a mock session object
    mock_session = MagicMock()
    mocker.patch('app.core.database.SessionLocal', return_value=mock_session)

    # Action: Call the get_db generator
    db_generator = get_db()
    
    # Assertions: The generator should yield the mock session
    assert next(db_generator) is mock_session
    
    # Assertions: After the generator is exhausted (e.g., in a with statement),
    # db.close() should be called.
    # The `next` call has not closed the session yet. Let's force it to close
    with pytest.raises(StopIteration):
        next(db_generator)
    
    # Now, assert that the close method was called
    mock_session.close.assert_called_once()
    
def test_get_db_closes_on_exception(mocker):
    """
    Tests that get_db correctly calls db.close() even when an exception is raised.
    """
    # Arrange: Mock the SessionLocal class to return a mock session object
    mock_session = MagicMock()
    mocker.patch('app.core.database.SessionLocal', return_value=mock_session)

    # Action: Call the get_db generator
    db_generator = get_db()
    
    # Assertions: Check that the generator yields the session
    db_instance = next(db_generator)

    # Simulate an exception within the try block
    db_instance.rollback.side_effect = Exception("Simulated processing error")
    
    # Assertions: Check that the generator still calls close()
    with pytest.raises(Exception) as exc_info:
        db_generator.throw(Exception("Simulated processing error"))
    
    assert "Simulated processing error" in str(exc_info.value)
    mock_session.close.assert_called_once()