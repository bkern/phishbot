from collections import Counter
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

IHOZ_BASE = "http://www.ihoz.com"  # HTTP only — SSL cert is expired on HTTPS


def _normalize_set(raw: str) -> str:
    raw = raw.strip()
    if raw == "E":
        return "Encore"
    if raw.isdigit():
        return f"Set {raw}"
    return raw or "Unknown"


@tool
def get_song_stats(song: str) -> dict:
    """Look up a Phish song's full play history from ihoz.com.

    Returns total times played, last played date, set distribution (Set 1 vs Set 2 tendency),
    the most common songs played immediately before and after it, and the 10 most recent performances.
    Use for gap questions ('when was Tweezer last played?'), transition questions ('what usually follows Carini?'),
    and set-type questions ('is Antelope a first set or second set song?').
    IMPORTANT: ihoz.com data lags behind real performances by weeks or months.
    For very recent plays, also call search_setlists or note the data may be incomplete.
    """
    url = f"{IHOZ_BASE}/cgi/phish?song={quote_plus(song)}&chart=on"
    try:
        response = httpx.get(url, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return {"song": song, "error": str(e), "source": "ihoz.com"}

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        return {"song": song, "times_played": 0, "error": "No data found", "source": "ihoz.com"}

    plays = []
    for row in table.find_all("tr")[1:]:  # skip header row
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        before_text = cells[4].get_text(strip=True)
        after_text = cells[5].get_text(strip=True)
        plays.append({
            "date": cells[0].get_text(strip=True),
            "gap": cells[1].get_text(strip=True),
            "set": _normalize_set(cells[2].get_text(strip=True)),
            "before": before_text if before_text != "***" else None,
            "after": after_text if after_text != "***" else None,
        })

    if not plays:
        return {"song": song, "times_played": 0, "source": "ihoz.com"}

    set_counts = Counter(p["set"] for p in plays)
    before_counts = Counter(p["before"] for p in plays if p["before"])
    after_counts = Counter(p["after"] for p in plays if p["after"])

    return {
        "song": song,
        "times_played": len(plays),
        # ihoz.com returns rows in ascending chronological order (oldest first)
        "last_played": plays[-1]["date"],
        "set_breakdown": dict(set_counts.most_common()),
        "top_before": [{"song": s, "count": c} for s, c in before_counts.most_common(5)],
        "top_after": [{"song": s, "count": c} for s, c in after_counts.most_common(5)],
        "recent_plays": plays[-10:],
        "source": "ihoz.com",
    }
