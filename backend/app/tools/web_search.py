# app/services/web_search.py
import httpx

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

def web_search_summary(
    query: str,
    max_results: int = 5,
    timeout_s: float = 12.0,
    engine: str = "google",   # or "google_news"
    hl: str = "zh-TW",        # UI language
    gl: str = "tw",           # Geo
) -> str:
    """
    Uses SerpAPI (Google engine) to fetch results and returns compact markdown:
    - [Title](URL) — snippet
    Returns "" if not configured or on failure.
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
