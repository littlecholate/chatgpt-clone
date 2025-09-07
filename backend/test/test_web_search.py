import pytest
import requests_mock
import json
import httpx
from httpx import Response
from unittest.mock import MagicMock
from app.tools.web_search import web_search_summary, SERPAPI_ENDPOINT, SERPAPI_KEY

def test_web_search_summary_with_news_engine(mocker):
    """
    Tests that the function handles a different engine and news results.
    """
    # Mock a response from the "google_news" engine
    mock_data = {
        "search_metadata": {"status": "OK"},
        "news_results": [
            {
                "title": "Breaking News",
                "link": "https://news.example.com/breaking",
                "snippet": "A major event occurred today.",
                "source": "News Outlet"
            }
        ]
    }
    
    # Define a handler function for the mock transport
    def mock_handler(request):
        # Assertions on the request parameters
        assert request.url.host == 'serpapi.com'
        assert 'engine=google_news' in str(request.url)
        return Response(200, json=mock_data)

    # Use httpx.MockTransport with the handler function
    mock_transport = httpx.MockTransport(mock_handler)
    
    # Use mocker to patch the httpx.Client class in the web_search module
    # This ensures that any new httpx.Client instance created inside the function
    # will use our mock transport.
    mocker.patch('app.tools.web_search.httpx.Client', return_value=httpx.Client(transport=mock_transport))

    # Action
    result = web_search_summary(query="latest news", engine="google_news")

    # Assertions
    expected_output = "- [Breaking News](https://news.example.com/breaking) — A major event occurred today."
    assert result == expected_output
    
def test_web_search_summary_success(mocker):
    """
    Tests that web_search_summary correctly formats results from a successful API call.
    """
    # Mock the SerpAPI response with a successful result
    mock_data = {
        "search_metadata": {"status": "OK"},
        "organic_results": [
            {
                "title": "FastAPI Framework",
                "link": "https://fastapi.tiangolo.com",
                "snippet": "A modern, fast web framework for building APIs with Python."
            },
            {
                "title": "Python Web Frameworks",
                "link": "https://www.python.org/doc/frameworks/",
                "snippet": "An overview of Python web development frameworks."
            }
        ]
    }
    
    # Create a mock response object
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = mock_data

    # Create a mock client that returns the mock response
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response
    
    # Configure the mock client to be a context manager
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    # Patch the httpx.Client class in your function to return the mock client
    mocker.patch('app.tools.web_search.httpx.Client', return_value=mock_client)
    
    # Action: Call the function
    query = "FastAPI"
    result = web_search_summary(query=query)

    # Assertions
    expected_output = (
        "- [FastAPI Framework](https://fastapi.tiangolo.com) — A modern, fast web framework for building APIs with Python."
        "\n- [Python Web Frameworks](https://www.python.org/doc/frameworks/) — An overview of Python web development frameworks."
    )
    assert result == expected_output

def test_web_search_summary_empty_results(mocker):  # Add mocker fixture
    """
    Tests that the function returns an empty string when SerpAPI returns no organic results.
    """
    # Mock the SerpAPI response with a successful but empty result
    mock_data = {"search_metadata": {"status": "OK"}, "organic_results": []}

    # Define a handler function for the mock transport
    def mock_handler(request):
        # The request is intercepted here. We return a successful response with empty data.
        return Response(200, json=mock_data)

    # Use httpx.MockTransport with the handler function
    mock_transport = httpx.MockTransport(mock_handler)
    
    # Use mocker to patch the httpx.Client class in the web_search module
    # This ensures that any new httpx.Client instance created inside the function
    # will use our mock transport.
    mocker.patch('app.tools.web_search.httpx.Client', return_value=httpx.Client(transport=mock_transport))

    # Action
    result = web_search_summary(query="nonexistent search")

    # Assertions
    assert result == ""
  
def test_web_search_summary_http_error(mocker):
    """
    Tests that the function handles HTTP errors gracefully.
    """
    # Define a function to handle the mock request
    def mock_handler(request):
        # Return a mock 500 Internal Server Error response
        return Response(500, text="Internal Server Error")

    # Use httpx.MockTransport with the mock handler
    mock_transport = httpx.MockTransport(mock_handler)
    
    # Action: Call the function with a client that uses the mock transport
    with httpx.Client(transport=mock_transport) as client:
        # Patch the httpx.Client in your function to use the mock transport
        # This is needed because your function creates a new client internally
        # You'll need to patch httpx.Client in the module where web_search_summary is defined
        mocker.patch('app.tools.web_search.httpx.Client', return_value=client)
        result = web_search_summary(query="error case")

    # Assertions
    assert result == ""

def test_web_search_summary_with_invalid_key(mocker):
    """
    Tests that the function returns an empty string when the SerpAPI key is empty.
    """
    # Mock the SERPAPI_KEY using the mocker fixture
    mocker.patch('app.tools.web_search.SERPAPI_KEY', "")

    # Action
    result = web_search_summary(query="test query")

    # Assertions
    assert result == ""
    """
    Tests that the function returns an empty string when the SerpAPI key is empty.
    """
    # Mock the SERPAPI_KEY to be an empty string
    mocker.patch('app.tools.web_search.SERPAPI_KEY', "")

    # Action
    result = web_search_summary(query="test query")
    
    # Assertions
    assert result == ""