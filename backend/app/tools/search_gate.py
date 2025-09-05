# app/services/search_gate.py
FRESH_KEYWORDS = (
    "latest", "today", "news", "update", "recent", "price", "release", "breaking",
    "現在", "最新", "新聞", "價格", "更新", "近況",
)

def should_search(user_text: str) -> bool:
    t = user_text.lower()
    return any(k in t for k in FRESH_KEYWORDS)