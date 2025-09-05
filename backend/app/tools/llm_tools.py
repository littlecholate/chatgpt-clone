# app/llm/tools.py
import json
from typing import Dict, Any, Optional
from app.services.web_search import web_search_summary

# 2.1 Tool schema (OpenAI / vLLM format)
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web and return a compact markdown list of sources and snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {
                    "type": "integer",
                    "description": "How many results to return (1-10)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
}

# 2.2 Run a tool call (returns a role='tool' message)
def run_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    fn = tool_call["function"]["name"]
    args_str = tool_call["function"].get("arguments") or "{}"
    try:
        args = json.loads(args_str)
    except Exception:
        args = {}
    if fn == "web_search":
        summary = web_search_summary(args.get("query", ""), int(args.get("max_results", 5)))
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": summary or "No results.",
        }
    # fallback
    return {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": f"Tool {fn} not implemented.",
    }

# 2.3 Buffer for incremental tool call args across streamed deltas
class ToolCallBuffer:
    """
    Accumulates partial tool_call deltas from streaming.
    You’ll collect into this until you can JSON-parse arguments.
    """
    def __init__(self) -> None:
        # id -> partial {id, type, function:{name, arguments(str)}}
        self._buf: Dict[str, Dict[str, Any]] = {}

    def add_delta(self, delta_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add one streamed 'tool_calls' delta item and return a fully-formed tool_call dict
        when ready (id, name, arguments complete), else None.
        """
        call_id = delta_call.get("id")
        if not call_id:
            return None

        slot = self._buf.setdefault(call_id, {"id": call_id, "type": "function", "function": {"name": "", "arguments": ""}})

        # merge name
        name_part = delta_call.get("function", {}).get("name")
        if name_part:
            slot["function"]["name"] += name_part

        # merge arguments (this arrives chunked)
        args_part = delta_call.get("function", {}).get("arguments")
        if args_part:
            slot["function"]["arguments"] += args_part

        # Heuristic: "ready" once we have a non-empty name and arguments parse as JSON
        name_ready = bool(slot["function"]["name"])
        args_ready = False
        if slot["function"]["arguments"]:
            try:
                json.loads(slot["function"]["arguments"])
                args_ready = True
            except Exception:
                args_ready = False

        if name_ready and args_ready:
            # pop and return a complete tool call
            return self._buf.pop(call_id)
        return None