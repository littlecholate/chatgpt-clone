# app/services/web_search.py
import os, httpx

TAVILY_API = "https://api.tavily.com/search"
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")

def web_search_summary(query: str, max_results: int = 5, timeout_s: float = 12.0) -> str:
    """
    Returns compact markdown bullets: - [Title](URL) — snippet
    Returns "" if not configured or on failure.
    """
    if not (TAVILY_KEY and query.strip()):
        return ""
    try:
        payload = {"api_key": TAVILY_KEY, "query": query, "max_results": max_results}
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(TAVILY_API, json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return ""

    results = data.get("results") or []
    lines = []
    for item in results[:max_results]:
        title = (item.get("title") or item.get("url") or "Result").strip()
        url = (item.get("url") or "").strip()
        snippet = (item.get("content") or "").replace("\n", " ").strip()[:240]
        if url:
            lines.append(f"- [{title}]({url}) — {snippet}")
    return "\n".join(lines)