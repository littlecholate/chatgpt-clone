# app/llm/tools.py
import json
from typing import Dict, Any, Optional
from .web_search import web_search_summary

# 2.1 Tool schema (OpenAI/vLLM format)
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
                "engine": {
                    "type": "string",
                    "description": "SerpAPI engine: google or google_news",
                    "enum": ["google", "google_news"],
                    "default": "google",
                },
                "hl": {"type": "string", "description": "UI lang, e.g. en or zh-TW", "default": "zh-TW"},
                "gl": {"type": "string", "description": "Geo, e.g. us or tw", "default": "tw"},
            },
            "required": ["query"],
        },
    },
}

# 2.2 Execute a tool call and return the required role='tool' message
def run_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    fn = tool_call["function"]["name"]
    args_str = tool_call["function"].get("arguments") or "{}"
    try:
        args = json.loads(args_str)
    except Exception:
        args = {}

    if fn == "web_search":
        summary = web_search_summary(
            query=args.get("query", ""),
            max_results=int(args.get("max_results", 5) or 5),
            engine=args.get("engine", "google"),
            hl=args.get("hl", "zh-TW"),
            gl=args.get("gl", "tw"),
        )
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"],  # must match the id from the assistant tool call
            "content": summary or "No results.",
        }

    return {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": f"Tool {fn} not implemented.",
    }

# 2.3 Buffer for incremental tool call args across streamed deltas
class ToolCallBuffer:
    """
    Accumulates partial tool_call deltas from streaming.
    Emits a complete tool_call dict when 'name' is set and 'arguments' parses as JSON.
    """
    def __init__(self) -> None:
        self._buf: Dict[str, Dict[str, Any]] = {}

    def add_delta(self, delta_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        call_id = delta_call.get("id")
        if not call_id:
            return None

        slot = self._buf.setdefault(
            call_id,
            {"id": call_id, "type": "function", "function": {"name": "", "arguments": ""}},
        )

        # append partial pieces
        name_part = delta_call.get("function", {}).get("name")
        if name_part:
            slot["function"]["name"] += name_part

        args_part = delta_call.get("function", {}).get("arguments")
        if args_part:
            slot["function"]["arguments"] += args_part

        # ready when name exists and arguments parse
        name_ready = bool(slot["function"]["name"])
        args_ready = False
        if slot["function"]["arguments"]:
            try:
                json.loads(slot["function"]["arguments"])
                args_ready = True
            except Exception:
                args_ready = False

        if name_ready and args_ready:
            return self._buf.pop(call_id)
        return None