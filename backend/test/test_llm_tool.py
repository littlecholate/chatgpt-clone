import pytest
import json
from app.tools.llm_tool import ToolCallBuffer

def test_add_delta_with_single_chunk_completes_call():
    """
    Tests that a single, complete delta chunk is correctly processed
    and the buffer returns the complete tool call.
    """
    buffer = ToolCallBuffer()
    
    # A single, complete delta chunk
    delta = {
        "id": "call_123",
        "function": {
            "name": "web_search",
            "arguments": '{"query": "best programming language"}'
        }
    }
    
    # Action
    complete_call = buffer.add_delta(delta)
    
    # Assertions
    assert complete_call is not None
    assert complete_call["id"] == "call_123"
    assert complete_call["function"]["name"] == "web_search"
    assert json.loads(complete_call["function"]["arguments"])["query"] == "best programming language"
    
def test_add_delta_with_multiple_chunks_reconstructs_call():
    """
    Tests that a tool call is correctly reconstructed from multiple,
    fragmented delta chunks.
    """
    buffer = ToolCallBuffer()
    
    # Simulate a streamed tool call
    chunks = [
        {"id": "call_456", "function": {"name": "web_search"}},
        {"id": "call_456", "function": {"arguments": '{"query": "fastapi'}},
        {"id": "call_456", "function": {"arguments": ' tutorial"}'}}
    ]
    
    # Action & Assertions
    # Process the first two chunks - the call should not be complete yet
    incomplete_call_1 = buffer.add_delta(chunks[0])
    assert incomplete_call_1 is None
    
    incomplete_call_2 = buffer.add_delta(chunks[1])
    assert incomplete_call_2 is None
    
    # Process the last chunk - the call should now be complete
    complete_call = buffer.add_delta(chunks[2])
    assert complete_call is not None
    assert complete_call["id"] == "call_456"
    assert complete_call["function"]["name"] == "web_search"
    assert complete_call["function"]["arguments"] == '{"query": "fastapi tutorial"}'

def test_add_delta_handles_multiple_concurrent_calls():
    """
    Tests that the buffer can handle chunks from multiple tool calls
    without mixing up the data.
    """
    buffer = ToolCallBuffer()
    
    # Simulate two interleaved tool calls
    chunk1_call_A = {"id": "call_A", "function": {"name": "web_search"}}
    chunk1_call_B = {"id": "call_B", "function": {"name": "web_search"}}
    chunk2_call_A = {"id": "call_A", "function": {"arguments": '{"query": "docker"}'}}
    chunk2_call_B = {"id": "call_B", "function": {"arguments": '{"query": "kubernetes"}'}}
    
    # Action: Process chunks out of order to test robustness
    buffer.add_delta(chunk1_call_A)
    buffer.add_delta(chunk1_call_B)
    
    complete_call_B = buffer.add_delta(chunk2_call_B)
    assert complete_call_B is not None
    assert complete_call_B["id"] == "call_B"
    
    complete_call_A = buffer.add_delta(chunk2_call_A)
    assert complete_call_A is not None
    assert complete_call_A["id"] == "call_A"
    
def test_add_delta_with_malformed_chunk_does_not_fail():
    """
    Tests that the buffer gracefully handles a delta chunk that
    is missing a required 'id' key.
    """
    buffer = ToolCallBuffer()
    
    # Simulate an incomplete or malformed delta
    delta = {"function": {"arguments": '{"query": "python"}'}}
    
    # Action
    result = buffer.add_delta(delta)
    
    # Assertions
    assert result is None
    assert buffer._buffer == {} # The buffer should remain empty