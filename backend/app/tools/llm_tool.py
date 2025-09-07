import json
import os
from typing import Dict, Any, List

# Note: In a real-world scenario, you would use a dedicated library
# like serpapi-python or a direct API call to your preferred search service.
# For this example, we'll use a placeholder function to demonstrate the
# structure of the tool.
def perform_web_search(query: str, num_results: int = 5) -> str:
    """
    A placeholder function to simulate a web search.
    In a production environment, this would call a service like SerpAPI.
    """
    # Replace with your actual SerpAPI logic or other search service
    print(f"Executing web search for: '{query}'")
    
    # You would use a library like `google-search-results`
    # from serpapi, or a custom HTTP request here.
    # For demonstration, we'll return a static result.
    
    # Example using a mock API call
    # from serpapi import GoogleSearch
    # params = {
    #   "engine": "google",
    #   "q": query,
    #   "api_key": os.getenv("SERPAPI_API_KEY")
    # }
    # search = GoogleSearch(params)
    # results = search.get_dict()
    # organic_results = results.get("organic_results", [])
    # formatted_results = json.dumps(organic_results[:num_results])

    # Since we can't make a live API call, we'll use a dummy result
    dummy_results = [
        {"title": "FastAPI: A modern, fast (high-performance) web framework", "link": "https://fastapi.tiangolo.com/", "snippet": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints."},
        {"title": "SerpAPI - The Real-time API to get Search Results from Google", "link": "https://serpapi.com/", "snippet": "SerpApi is a real-time API to get search results from Google, Bing, Yahoo, and more. It offers a variety of search engines and tools."},
        {"title": "Docker: Accelerated, Containerized Application Development", "link": "https://www.docker.com/", "snippet": "Docker provides software developers with a secure, reliable platform for building and running containerized applications."},
    ]

    formatted_results = json.dumps(dummy_results, indent=2)
    return formatted_results


# Define the tool's schema as required by the LLM
WEB_SEARCH_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Performs a web search using a search engine like Google.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query."
                },
                "num_results": {
                    "type": "integer",
                    "description": "The number of search results to return.",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}


class ToolCallBuffer:
    """
    Helper class to reconstruct complete tool call objects from a streaming response.
    """
    def __init__(self):
        self._buffer: Dict[str, Dict[str, Any]] = {}

    def add_delta(self, delta: Dict[str, Any]) -> Dict[str, Any] | None:
        """Adds a delta chunk and returns a complete tool call if available."""
        if "id" not in delta:
            return None
        
        tool_call_id = delta["id"]
        
        if tool_call_id not in self._buffer:
            self._buffer[tool_call_id] = {
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": "",
                    "arguments": ""
                }
            }
        
        # Append name and arguments
        if "name" in delta["function"]:
            self._buffer[tool_call_id]["function"]["name"] += delta["function"]["name"]
        if "arguments" in delta["function"]:
            self._buffer[tool_call_id]["function"]["arguments"] += delta["function"]["arguments"]

        # Check for completion (the `arguments` field is usually the last)
        # This is a heuristic; more robust logic might be needed for other models
        if "arguments" in delta["function"] and delta["function"]["arguments"].endswith("}"):
            complete_tool_call = self._buffer.pop(tool_call_id)
            return complete_tool_call
            
        return None

def run_tool_call(tool_call: Dict[str, Any]) -> Dict[str, str]:
    """
    Executes a tool call and returns a tool message to append to the history.
    """
    name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])
    
    # Dispatch the tool based on its name
    if name == "web_search":
        result = perform_web_search(
            query=arguments.get("query"),
            num_results=arguments.get("num_results", 5)
        )
        # Return a message in the format expected by the LLM
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": result,
        }
    else:
        # Handle unknown tools
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": f"Error: Unknown tool {name}",
        }