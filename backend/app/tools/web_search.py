# app/services/web_search.py
import os
import httpx

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
SERPAPI_KEY = "2bc8a7241a4fd9aea8b963a22d1b419864dfaa5ac1b0a6b2107101d3275dc631"

def web_search_summary(
    query: str,
    max_results: int = 5,
    timeout_s: float = 12.0,
    engine: str = "google",   # or "google_news"
    hl: str = "zh-TW",        # UI language
    gl: str = "tw",           # Geo
) -> str:
    """
    Use SerpAPI to fetch results and return compact markdown:
      - [Title](URL) — snippet
    Returns "" if SERPAPI_API_KEY missing, query empty, or request fails.
    """
    if not (SERPAPI_KEY and query.strip()):
        return ""

    params = {
        "engine": engine,
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": max(1, min(max_results, 10)),
        "hl": hl,
        "gl": gl,
    }

    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(SERPAPI_ENDPOINT, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return ""

    results = data.get("organic_results") or data.get("news_results") or []
    if not results:
        return ""

    bullets = []
    for item in results[:max_results]:
        title = (item.get("title") or item.get("link") or "Result").strip()
        url = (item.get("link") or item.get("link_url") or "").strip()
        snippet = (
            item.get("snippet")
            or item.get("excerpt")
            or item.get("content")
            or ""
        ).replace("\n", " ").strip()[:240]
        if url:
            bullets.append(f"- [{title}]({url}) — {snippet}")
    return "\n".join(bullets)