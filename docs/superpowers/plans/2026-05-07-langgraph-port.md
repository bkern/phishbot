# LangGraph Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hand-rolled `while True` ReAct loop in `backend/agent.py` with a LangGraph `StateGraph`, porting tool definitions to `@tool` decorators.

**Architecture:** Two-node `StateGraph(MessagesState)` — an `agent` node that calls `ChatAnthropic` with tools bound, and a `tools` node (`ToolNode`) that dispatches tool calls. A `tools_condition` conditional edge routes back to `agent` until no tool calls remain, then routes to `END`. The FastAPI interface in `main.py` is unchanged.

**Tech Stack:** `langgraph`, `langchain-anthropic`, `langchain-core` (new); existing `fastapi`, `anthropic`, `httpx` (unchanged).

---

## File Map

| File | Change |
|---|---|
| `backend/requirements.txt` | Add 3 new packages |
| `backend/tools/setlistfm.py` | Add `@tool`, remove `TOOL_DEFINITION` dict |
| `backend/tools/phishnet.py` | Add `@tool` to 3 functions, remove 3 dict exports |
| `backend/tools/discography.py` | Add `@tool` to `search_discography`, remove dict |
| `backend/tools/ihoz.py` | Add `@tool` to `get_song_stats`, remove dict |
| `backend/agent.py` | Full rewrite — `StateGraph` replaces `while True` |
| `backend/tests/test_setlistfm.py` | `.invoke({})` calls, replace dict shape test |
| `backend/tests/test_phishnet.py` | `.invoke({})` calls, replace 3 dict shape tests |
| `backend/tests/test_discography.py` | `.invoke({})` calls, replace dict shape test |
| `backend/tests/test_ihoz.py` | `.invoke({})` calls, replace dict shape test |
| `backend/tests/test_agent.py` | Full rewrite for `_app.invoke()` interface |

---

## Task 1: Create branch and install dependencies

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Create the feature branch**

```bash
git checkout -b feat/langgraph
```

Expected: `Switched to a new branch 'feat/langgraph'`

- [ ] **Step 2: Add new packages to requirements.txt**

In `backend/requirements.txt`, add after the existing lines:

```
langgraph>=0.2.0
langchain-anthropic>=0.3.0
langchain-core>=0.3.0
```

- [ ] **Step 3: Install**

```bash
cd backend && source .venv/bin/activate && pip install -r requirements.txt
```

Expected: packages install without errors; `langgraph`, `langchain-anthropic`, `langchain-core` appear in the output.

- [ ] **Step 4: Verify imports work**

```bash
python -c "import langgraph; import langchain_anthropic; import langchain_core; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add langgraph, langchain-anthropic, langchain-core"
```

---

## Task 2: Convert setlistfm.py to @tool

The `@tool` decorator (from `langchain_core.tools`) wraps the function in a `StructuredTool`. It uses the **docstring** as the description and **type annotations** as the schema. After this, call the tool via `search_setlists.invoke({"year": "2024"})` instead of `search_setlists(year="2024")`.

**Files:**
- Modify: `backend/tools/setlistfm.py`
- Modify: `backend/tests/test_setlistfm.py`

- [ ] **Step 1: Rewrite setlistfm.py**

Replace the entire file content with:

```python
import os
from typing import Optional, Literal
import httpx
from langchain_core.tools import tool

SETLISTFM_BASE = "https://api.setlist.fm/rest/1.0"


@tool
def search_setlists(
    year: Optional[str] = None,
    song: Optional[str] = None,
    date: Optional[str] = None,
    position: Literal["opener", "closer", "any"] = "any",
) -> dict:
    """Search Phish setlists by year, song name, or specific date.

    Use 'date' (YYYY-MM-DD) to get the full setlist for a specific show — all songs, all sets.
    Use 'song' to find all shows where a song was played.
    Use 'position' ('opener', 'closer', or 'any') to filter by set position.
    Use 'year' to narrow results to a specific year.
    """
    params = {"artistName": "Phish", "p": 1}
    if year:
        params["year"] = year
    if song:
        params["songName"] = song
    if date:
        # setlist.fm expects DD-MM-YYYY; we accept YYYY-MM-DD from Claude
        try:
            y, m, d = date.split("-")
            params["date"] = f"{d}-{m}-{y}"
        except ValueError:
            pass

    response = httpx.get(
        f"{SETLISTFM_BASE}/search/setlists",
        headers={
            "x-api-key": os.environ["SETLISTFM_API_KEY"],
            "Accept": "application/json",
        },
        params=params,
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for setlist in data.get("setlist", [])[:20]:
        show_date = setlist.get("eventDate", "")
        venue_obj = setlist.get("venue", {})
        venue = f"{venue_obj.get('name', '')}, {venue_obj.get('city', {}).get('name', '')}"

        non_encore_idx = 0
        sets_data = []
        main_songs = []
        all_songs = []

        for set_data in setlist.get("sets", {}).get("set", []):
            is_encore = bool(set_data.get("encore", 0))
            if is_encore:
                set_label = "Encore"
            else:
                non_encore_idx += 1
                set_label = f"Set {non_encore_idx}"

            set_song_names = []
            for song_obj in set_data.get("song", []):
                name = song_obj.get("name", "")
                entry = {"name": name, "encore": is_encore, "set": set_label}
                all_songs.append(entry)
                set_song_names.append(name)
                if not is_encore:
                    main_songs.append(entry)

            if set_song_names:
                sets_data.append({"label": set_label, "songs": set_song_names})

        opener = main_songs[:1]
        closer = main_songs[-1:] if main_songs else []

        if position == "opener":
            candidates = opener
        elif position == "closer":
            candidates = closer
        else:
            candidates = all_songs

        if song:
            candidates = [s for s in candidates if song.lower() in s["name"].lower()]
            if not candidates:
                continue

        result = {"date": show_date, "venue": venue, "songs": candidates}

        if date and not song:
            result["sets"] = sets_data

        results.append(result)

    return {"total": data.get("total", 0), "results": results, "source": "setlist.fm"}
```

- [ ] **Step 2: Update test_setlistfm.py**

Replace the entire file content with:

```python
from unittest.mock import patch, MagicMock

SAMPLE_SETLIST = {
    "eventDate": "01-08-2024",
    "venue": {
        "name": "Merriweather Post Pavilion",
        "city": {"name": "Columbia"},
    },
    "sets": {
        "set": [
            {
                "encore": 0,
                "song": [
                    {"name": "Sigma Oasis"},
                    {"name": "Tweezer"},
                    {"name": "Chalk Dust Torture"},
                ],
            },
            {
                "encore": 1,
                "song": [{"name": "Tweezer Reprise"}],
            },
        ]
    },
}


def _mock_response(setlists: list) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"total": len(setlists), "setlist": setlists}
    mock.raise_for_status = MagicMock()
    return mock


def test_search_setlists_tool_name():
    from tools.setlistfm import search_setlists
    assert search_setlists.name == "search_setlists"


def test_search_setlists_tool_has_year_song_position_args():
    from tools.setlistfm import search_setlists
    schema = search_setlists.args_schema.schema()
    props = schema["properties"]
    assert "year" in props
    assert "song" in props
    assert "position" in props


def test_search_returns_source():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({})
    assert result["source"] == "setlist.fm"


def test_search_returns_date_and_venue():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({})
    assert result["results"][0]["date"] == "01-08-2024"
    assert "Merriweather" in result["results"][0]["venue"]


def test_search_by_song_filters_to_matching_songs():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({"song": "Tweezer"})
    matched = [s["name"] for s in result["results"][0]["songs"]]
    assert "Tweezer" in matched
    assert "Sigma Oasis" not in matched


def test_search_opener_returns_first_non_encore_song():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({"position": "opener"})
    songs = result["results"][0]["songs"]
    assert len(songs) == 1
    assert songs[0]["name"] == "Sigma Oasis"


def test_search_closer_returns_last_non_encore_song():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({"position": "closer"})
    songs = result["results"][0]["songs"]
    assert len(songs) == 1
    assert songs[0]["name"] == "Chalk Dust Torture"


def test_search_passes_year_param_to_api():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([])) as mock_get:
        search_setlists.invoke({"year": "2024"})
    assert mock_get.call_args[1]["params"]["year"] == "2024"


def test_empty_results():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([])):
        result = search_setlists.invoke({"song": "Nonexistent Song XYZ"})
    assert result["results"] == []
    assert result["total"] == 0


def test_search_by_song_and_position_filters_correctly():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({"song": "Sigma Oasis", "position": "opener"})
    assert len(result["results"]) == 1
    assert result["results"][0]["songs"][0]["name"] == "Sigma Oasis"

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({"song": "Tweezer", "position": "opener"})
    assert result["results"] == []


def test_search_includes_encore_songs_in_any_position():
    from tools.setlistfm import search_setlists
    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists.invoke({"song": "Tweezer"})
    song_names = [s["name"] for s in result["results"][0]["songs"]]
    assert "Tweezer" in song_names
    assert "Tweezer Reprise" in song_names
    encore_flags = {s["name"]: s["encore"] for s in result["results"][0]["songs"]}
    assert encore_flags["Tweezer"] == False
    assert encore_flags["Tweezer Reprise"] == True
```

- [ ] **Step 3: Run tests**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_setlistfm.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tools/setlistfm.py backend/tests/test_setlistfm.py
git commit -m "refactor: convert setlistfm to @tool decorator"
```

---

## Task 3: Convert phishnet.py to @tool

**Files:**
- Modify: `backend/tools/phishnet.py`
- Modify: `backend/tests/test_phishnet.py`

- [ ] **Step 1: Rewrite phishnet.py**

Replace the entire file content with:

```python
import os
import re
from typing import Optional
from urllib.parse import quote as url_quote
import httpx
from langchain_core.tools import tool

PHISHNET_BASE = "https://api.phish.net/v5"


def _song_to_slug(song: str) -> str:
    # Take only the first song if a segue notation like "Tweezer > Lifeboy" is passed
    song = song.split(">")[0]
    slug = song.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


@tool
def get_jamcharts(song: str) -> dict:
    """Get community jam charts for a Phish song — notable, highly-rated performances with track durations.

    Use for questions about the best or longest versions of a song, or must-hear jams.
    Returns each jam's date, venue, set, duration, and notes.
    """
    slug = _song_to_slug(song)
    response = httpx.get(
        f"{PHISHNET_BASE}/jamcharts/slug/{slug}.json",
        params={"apikey": os.environ["PHISHNET_API_KEY"]},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    jams = []
    for entry in data.get("data", []):
        jam = {
            "date": entry.get("showdate", ""),
            "venue": f"{entry.get('venue', '')}, {entry.get('city', '')}, {entry.get('state', '')}",
            "set": entry.get("set", ""),
            "duration": entry.get("tracktime", ""),
        }
        notes = entry.get("jamnotesshort", "").strip()
        if notes:
            jam["notes"] = notes
        jams.append(jam)

    return {"song": song, "total": data.get("total", len(jams)), "jams": jams, "source": "phish.net"}


@tool
def get_song_history(song: str) -> dict:
    """Get the history, background, and metadata for a Phish song from phish.net's editorial database.

    Use for questions about a song's origins, meaning, story, or lyrics.
    """
    slug = _song_to_slug(song)
    response = httpx.get(
        f"{PHISHNET_BASE}/songdata/slug/{slug}.json",
        params={"apikey": os.environ["PHISHNET_API_KEY"]},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    entries = data.get("data", [])
    if not entries:
        return {"song": None, "history": None, "source": "phish.net"}

    entry = entries[0]
    return {
        "song": entry.get("song"),
        "history": entry.get("history") or None,
        "lyrics": entry.get("lyrics") or None,
        "source": "phish.net",
    }


def _shows_from_setlistfm(venue: str) -> list[dict]:
    """Venue-by-name search via setlist.fm (phish.net venue endpoint is access-restricted)."""
    response = httpx.get(
        "https://api.setlist.fm/rest/1.0/search/setlists",
        headers={
            "x-api-key": os.environ["SETLISTFM_API_KEY"],
            "Accept": "application/json",
        },
        params={"artistName": "Phish", "venueName": venue, "p": 1},
        timeout=10.0,
    )
    response.raise_for_status()
    shows = []
    for s in response.json().get("setlist", []):
        # setlist.fm returns dates as DD-MM-YYYY — convert to YYYY-MM-DD
        raw_date = s.get("eventDate", "")
        try:
            d, m, y = raw_date.split("-")
            showdate = f"{y}-{m}-{d}"
        except ValueError:
            showdate = raw_date
        venue_obj = s.get("venue", {})
        city_obj = venue_obj.get("city", {})
        shows.append({
            "showdate": showdate,
            "venue": venue_obj.get("name", ""),
            "city": city_obj.get("name", ""),
            "state": city_obj.get("stateCode", ""),
        })
    return shows


@tool
def search_shows(
    state: Optional[str] = None,
    venue: Optional[str] = None,
    year: Optional[str] = None,
) -> dict:
    """Search Phish shows by US state or venue name.

    Use for questions like 'how many shows in Minnesota', 'what venues has Phish played in Colorado',
    or 'all shows at Madison Square Garden'.
    Provide state (2-letter abbreviation) OR venue name — not both.
    Optionally filter by year.
    """
    try:
        if venue:
            # phish.net venue-by-name endpoint is access-restricted; use setlist.fm instead
            all_shows = _shows_from_setlistfm(venue)

        elif state:
            response = httpx.get(
                f"{PHISHNET_BASE}/shows/state/{state}.json",
                params={"apikey": os.environ["PHISHNET_API_KEY"]},
                timeout=10.0,
            )
            response.raise_for_status()
            raw = response.json().get("data", [])
            # phish.net returns shows for all artists — filter to Phish only
            all_shows = [
                {
                    "showdate": s.get("showdate", ""),
                    "venue": s.get("venue", ""),
                    "city": s.get("city", ""),
                    "state": s.get("state", ""),
                }
                for s in raw
                if s.get("artist_name", "").lower() == "phish"
            ]

        else:
            return {"shows": [], "total": 0, "source": "phish.net"}

    except httpx.HTTPStatusError as e:
        return {"shows": [], "total": 0, "source": "phish.net",
                "error": f"API error: {e.response.status_code}"}

    if year:
        all_shows = [s for s in all_shows if s.get("showdate", "").startswith(year)]

    shows = [
        {
            "date": s.get("showdate", ""),
            "venue": s.get("venue", ""),
            "city": s.get("city", ""),
            "state": s.get("state", ""),
        }
        for s in all_shows
    ]

    return {"shows": shows, "total": len(shows), "source": "phish.net"}
```

- [ ] **Step 2: Update test_phishnet.py**

Replace the entire file content with:

```python
from unittest.mock import patch, MagicMock


def _mock_response(data: list, total: int = None) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {
        "error": False,
        "total": total if total is not None else len(data),
        "data": data,
    }
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JAMCHART_DATA = [
    {
        "showid": "1234567890",
        "showdate": "1994-07-08",
        "venue": "Great Woods Center",
        "city": "Mansfield",
        "state": "MA",
        "set": "2",
        "tracktime": "38:23",
        "recommended": 1,
        "jamnotesshort": "Epic segue into Lifeboy",
    },
    {
        "showid": "0987654321",
        "showdate": "1997-11-22",
        "venue": "Hampton Coliseum",
        "city": "Hampton",
        "state": "VA",
        "set": "2",
        "tracktime": "31:07",
        "recommended": 1,
        "jamnotesshort": "",
    },
]

SAMPLE_SONGDATA = [
    {
        "songid": "432",
        "song": "Tweezer",
        "slug": "tweezer",
        "nickname": "",
        "history": "Debuted on January 20, 1990 at University of Vermont. "
                   "A vehicle for extended improvisation.",
        "lyrics": "Step into the freezer...",
    }
]


def test_get_jamcharts_tool_name():
    from tools.phishnet import get_jamcharts
    assert get_jamcharts.name == "get_jamcharts"


def test_get_song_history_tool_name():
    from tools.phishnet import get_song_history
    assert get_song_history.name == "get_song_history"


def test_search_shows_tool_name():
    from tools.phishnet import search_shows
    assert search_shows.name == "search_shows"


def test_search_shows_tool_has_state_venue_year_args():
    from tools.phishnet import search_shows
    schema = search_shows.args_schema.schema()
    props = schema["properties"]
    assert "state" in props
    assert "venue" in props
    assert "year" in props


def test_song_to_slug_simple():
    from tools.phishnet import _song_to_slug
    assert _song_to_slug("Tweezer") == "tweezer"


def test_song_to_slug_multi_word():
    from tools.phishnet import _song_to_slug
    assert _song_to_slug("Bathtub Gin") == "bathtub-gin"
    assert _song_to_slug("You Enjoy Myself") == "you-enjoy-myself"
    assert _song_to_slug("Chalk Dust Torture") == "chalk-dust-torture"


def test_song_to_slug_strips_segue_notation():
    from tools.phishnet import _song_to_slug
    assert _song_to_slug("Tweezer > Lifeboy") == "tweezer"


def test_get_jamcharts_returns_source():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts.invoke({"song": "Tweezer"})
    assert result["source"] == "phish.net"


def test_get_jamcharts_returns_jams_with_date_venue_duration():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts.invoke({"song": "Tweezer"})
    jam = result["jams"][0]
    assert jam["date"] == "1994-07-08"
    assert "Great Woods" in jam["venue"]
    assert jam["duration"] == "38:23"


def test_get_jamcharts_includes_notes_when_present():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts.invoke({"song": "Tweezer"})
    assert result["jams"][0]["notes"] == "Epic segue into Lifeboy"


def test_get_jamcharts_omits_notes_when_empty():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts.invoke({"song": "Tweezer"})
    assert "notes" not in result["jams"][1]


def test_get_jamcharts_passes_slug_to_api():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])) as mock_get:
        get_jamcharts.invoke({"song": "Bathtub Gin"})
    url = mock_get.call_args[0][0]
    assert "bathtub-gin" in url


def test_get_jamcharts_includes_set_field():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts.invoke({"song": "Tweezer"})
    assert result["jams"][0]["set"] == "2"


def test_get_jamcharts_includes_total():
    from tools.phishnet import get_jamcharts
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA, total=47)):
        result = get_jamcharts.invoke({"song": "Tweezer"})
    assert result["total"] == 47


def test_get_song_history_returns_source():
    from tools.phishnet import get_song_history
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SONGDATA)):
        result = get_song_history.invoke({"song": "Tweezer"})
    assert result["source"] == "phish.net"


def test_get_song_history_returns_name_and_history():
    from tools.phishnet import get_song_history
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SONGDATA)):
        result = get_song_history.invoke({"song": "Tweezer"})
    assert result["song"] == "Tweezer"
    assert "1990" in result["history"]


def test_get_song_history_returns_not_found_when_empty():
    from tools.phishnet import get_song_history
    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = get_song_history.invoke({"song": "Nonexistent XYZ"})
    assert result["song"] is None
    assert result["history"] is None


def test_get_song_history_not_found_includes_source():
    from tools.phishnet import get_song_history
    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = get_song_history.invoke({"song": "Nonexistent XYZ"})
    assert result["source"] == "phish.net"


# ── search_shows tests ────────────────────────────────────────────────────────

SAMPLE_SHOWS = [
    {
        "showdate": "2023-07-15",
        "venue": "Target Center",
        "city": "Minneapolis",
        "state": "MN",
        "country": "USA",
        "artist_name": "Phish",
    },
    {
        "showdate": "2019-08-02",
        "venue": "Xcel Energy Center",
        "city": "Saint Paul",
        "state": "MN",
        "country": "USA",
        "artist_name": "Phish",
    },
]

SAMPLE_SETLISTFM_SHOWS = [
    {
        "eventDate": "15-07-2023",
        "venue": {
            "name": "Madison Square Garden",
            "city": {"name": "New York", "stateCode": "NY"},
        },
    }
]


def test_search_shows_by_state_returns_source():
    from tools.phishnet import search_shows
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows.invoke({"state": "MN"})
    assert result["source"] == "phish.net"


def test_search_shows_by_state_returns_shows_with_correct_fields():
    from tools.phishnet import search_shows
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows.invoke({"state": "MN"})
    show = result["shows"][0]
    assert show["date"] == "2023-07-15"
    assert show["venue"] == "Target Center"
    assert show["city"] == "Minneapolis"
    assert show["state"] == "MN"


def test_search_shows_by_state_passes_state_to_url():
    from tools.phishnet import search_shows
    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])) as mock_get:
        search_shows.invoke({"state": "CO"})
    url = mock_get.call_args[0][0]
    assert "CO" in url


def test_search_shows_returns_total_count():
    from tools.phishnet import search_shows
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows.invoke({"state": "MN"})
    assert result["total"] == 2


def test_search_shows_by_state_filters_by_year():
    from tools.phishnet import search_shows
    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows.invoke({"state": "MN", "year": "2023"})
    assert result["total"] == 1
    assert result["shows"][0]["date"] == "2023-07-15"


def test_search_shows_by_venue_makes_one_api_call():
    from tools.phishnet import search_shows
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"setlist": SAMPLE_SETLISTFM_SHOWS}
    mock_resp.raise_for_status = MagicMock()
    with patch("tools.phishnet.httpx.get", return_value=mock_resp) as mock_get:
        result = search_shows.invoke({"venue": "Madison Square Garden"})
    assert mock_get.call_count == 1
    assert result["source"] == "phish.net"
    assert result["shows"][0]["date"] == "2023-07-15"
    assert result["shows"][0]["venue"] == "Madison Square Garden"


def test_search_shows_by_venue_passes_venue_name_to_api():
    from tools.phishnet import search_shows
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"setlist": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("tools.phishnet.httpx.get", return_value=mock_resp) as mock_get:
        search_shows.invoke({"venue": "Deer Creek"})
    call_params = mock_get.call_args[1]["params"]
    assert call_params["venueName"] == "Deer Creek"


def test_search_shows_venue_not_found_returns_empty():
    from tools.phishnet import search_shows
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"setlist": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("tools.phishnet.httpx.get", return_value=mock_resp):
        result = search_shows.invoke({"venue": "Nonexistent Venue XYZ"})
    assert result["shows"] == []
    assert result["total"] == 0
    assert result["source"] == "phish.net"
```

- [ ] **Step 3: Run tests**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_phishnet.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tools/phishnet.py backend/tests/test_phishnet.py
git commit -m "refactor: convert phishnet tools to @tool decorator"
```

---

## Task 4: Convert discography.py to @tool

**Files:**
- Modify: `backend/tools/discography.py`
- Modify: `backend/tests/test_discography.py`

- [ ] **Step 1: Add @tool to discography.py**

In `backend/tools/discography.py`, make two changes:

1. Add import at the top (after `from typing import Optional`):
```python
from langchain_core.tools import tool
```

2. Delete the `SEARCH_DISCOGRAPHY_TOOL` dict (lines 167–190 in the original file).

3. Add `@tool` decorator immediately above `def search_discography(`:
```python
@tool
def search_discography(
    song: Optional[str] = None,
    album: Optional[str] = None,
) -> dict:
    """Look up Phish studio albums and song origins.

    Use 'song' to find which album a song appears on.
    Use 'album' to get the tracklist and release year for an album.
    Call with no parameters to list all studio albums.
    Covers all studio releases from The White Tape (1984) through Sigma Oasis (2020).
    """
```

The function body is unchanged.

- [ ] **Step 2: Update test_discography.py**

Replace the entire file content with:

```python
def test_search_discography_tool_name():
    from tools.discography import search_discography
    assert search_discography.name == "search_discography"


def test_search_discography_tool_has_song_and_album_args():
    from tools.discography import search_discography
    schema = search_discography.args_schema.schema()
    props = schema["properties"]
    assert "song" in props
    assert "album" in props


def test_song_lookup_finds_correct_album():
    from tools.discography import search_discography
    result = search_discography.invoke({"song": "Kill Devil Falls"})
    assert len(result["matches"]) == 1
    assert result["matches"][0]["album"] == "Joy"
    assert result["matches"][0]["year"] == 2009


def test_song_lookup_is_case_insensitive():
    from tools.discography import search_discography
    result = search_discography.invoke({"song": "kill devil falls"})
    assert len(result["matches"]) == 1
    assert result["matches"][0]["album"] == "Joy"


def test_song_lookup_partial_match():
    from tools.discography import search_discography
    result = search_discography.invoke({"song": "Number Line"})
    assert any("Backwards Down the Number Line" in m["song"] for m in result["matches"])


def test_song_lookup_not_found_returns_empty():
    from tools.discography import search_discography
    result = search_discography.invoke({"song": "Nonexistent Song XYZ"})
    assert result["matches"] == []
    assert result["source"] == "discography"


def test_album_lookup_returns_year_and_tracklist():
    from tools.discography import search_discography
    result = search_discography.invoke({"album": "Rift"})
    assert len(result["albums"]) == 1
    album = result["albums"][0]
    assert album["year"] == 1993
    assert "Maze" in album["songs"]
    assert "Horn" in album["songs"]


def test_album_lookup_is_case_insensitive():
    from tools.discography import search_discography
    result = search_discography.invoke({"album": "farmhouse"})
    assert len(result["albums"]) == 1
    assert result["albums"][0]["title"] == "Farmhouse"


def test_album_lookup_partial_match():
    from tools.discography import search_discography
    result = search_discography.invoke({"album": "Picture of Nectar"})
    assert len(result["albums"]) == 1
    assert result["albums"][0]["year"] == 1992


def test_album_lookup_not_found_returns_empty():
    from tools.discography import search_discography
    result = search_discography.invoke({"album": "Nonexistent Album XYZ"})
    assert result["albums"] == []
    assert result["source"] == "discography"


def test_no_params_returns_all_albums():
    from tools.discography import search_discography
    result = search_discography.invoke({})
    assert len(result["albums"]) >= 10
    titles = [a["title"] for a in result["albums"]]
    assert "Junta" in titles
    assert "Joy" in titles
    assert "Sigma Oasis" in titles


def test_returns_source():
    from tools.discography import search_discography
    assert search_discography.invoke({"song": "Maze"})["source"] == "discography"
    assert search_discography.invoke({"album": "Rift"})["source"] == "discography"
    assert search_discography.invoke({})["source"] == "discography"
```

- [ ] **Step 3: Run tests**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_discography.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tools/discography.py backend/tests/test_discography.py
git commit -m "refactor: convert discography to @tool decorator"
```

---

## Task 5: Convert ihoz.py to @tool

**Files:**
- Modify: `backend/tools/ihoz.py`
- Modify: `backend/tests/test_ihoz.py`

- [ ] **Step 1: Add @tool to ihoz.py**

In `backend/tools/ihoz.py`, make two changes:

1. Add import at the top (after existing imports):
```python
from langchain_core.tools import tool
```

2. Delete the `GET_SONG_STATS_TOOL` dict (lines 8–33 in the original file).

3. Add `@tool` decorator and docstring immediately above `def get_song_stats(`:
```python
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
```

The function body is unchanged.

- [ ] **Step 2: Update test_ihoz.py**

Replace the entire file content with:

```python
from unittest.mock import patch, MagicMock

FIXTURE_HTML = """
<html><body>
<h1>Tweezer</h1>
<strong>Times played</strong>
<table border=1>
<tr><th>Date</th><th>Gap</th><th>Set</th><th>Pos.</th><th>Before</th><th>After</th></tr>
<tr><td>3/28/90</td><td>214</td><td>1</td><td>5/12</td>
  <td><a href="/cgi/phish?song=Walk+Away">Walk Away</a></td>
  <td><a href="/cgi/phish?song=Uncle+Pen">Uncle Pen</a></td></tr>
<tr><td>4/5/90</td><td>3</td><td>2</td><td>6/13</td>
  <td><a href="/cgi/phish?song=Donna+Lee">Donna Lee</a></td>
  <td><a href="/cgi/phish?song=Fee">Fee</a></td></tr>
<tr><td>4/7/90</td><td>2</td><td>1</td><td>10/13</td>
  <td><a href="/cgi/phish?song=Possum">Possum</a></td>
  <td><a href="/cgi/phish?song=Mike%27s+Song">Mike's Song</a></td></tr>
<tr><td>6/2/90</td><td>5</td><td>E</td><td>1/2</td>
  <td>***</td>
  <td><a href="/cgi/phish?song=Divided+Sky">Divided Sky</a></td></tr>
<tr><td>12/31/25</td><td>6</td><td>3</td><td>4/6</td>
  <td><a href="/cgi/phish?song=Auld+Lang+Syne">Auld Lang Syne</a></td>
  <td><a href="/cgi/phish?song=Piper">Piper</a></td></tr>
</table>
</body></html>
"""


def _mock_get(html: str = FIXTURE_HTML) -> MagicMock:
    mock = MagicMock()
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_get_song_stats_tool_name():
    from tools.ihoz import get_song_stats
    assert get_song_stats.name == "get_song_stats"


def test_get_song_stats_tool_has_song_arg():
    from tools.ihoz import get_song_stats
    schema = get_song_stats.args_schema.schema()
    assert "song" in schema["properties"]
    assert "song" in schema.get("required", [])


def test_returns_times_played():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert result["times_played"] == 5


def test_returns_last_played():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert result["last_played"] == "12/31/25"


def test_returns_source():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert result["source"] == "ihoz.com"


def test_set_breakdown_counts_correctly():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    breakdown = result["set_breakdown"]
    assert breakdown["Set 1"] == 2
    assert breakdown["Set 2"] == 1
    assert breakdown["Encore"] == 1
    assert breakdown["Set 3"] == 1


def test_set_breakdown_normalizes_encore():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert "Encore" in result["set_breakdown"]
    assert "E" not in result["set_breakdown"]


def test_top_after_counts_correctly():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    after_songs = [e["song"] for e in result["top_after"]]
    assert "Uncle Pen" in after_songs
    assert "Fee" in after_songs


def test_before_skips_unknown_marker():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    before_songs = [e["song"] for e in result["top_before"]]
    assert "***" not in before_songs


def test_recent_plays_returns_last_ten_or_fewer():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert len(result["recent_plays"]) <= 10
    assert result["recent_plays"][-1]["date"] == "12/31/25"


def test_recent_plays_entry_shape():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    play = result["recent_plays"][0]
    assert "date" in play
    assert "gap" in play
    assert "set" in play
    assert "before" in play
    assert "after" in play


def test_url_encodes_multi_word_song():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()) as mock_get:
        get_song_stats.invoke({"song": "Bathtub Gin"})
    url = mock_get.call_args[0][0]
    assert "Bathtub+Gin" in url or "Bathtub%20Gin" in url


def test_http_error_returns_error_dict():
    from tools.ihoz import get_song_stats
    import httpx
    with patch("tools.ihoz.httpx.get", side_effect=httpx.HTTPError("connection failed")):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert "error" in result
    assert result["source"] == "ihoz.com"
```

- [ ] **Step 3: Run tests**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_ihoz.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tools/ihoz.py backend/tests/test_ihoz.py
git commit -m "refactor: convert ihoz to @tool decorator"
```

---

## Task 6: Write failing tests for the LangGraph agent

These tests are written against the new `agent.py` interface **before** implementing it. They will fail until Task 7 is complete — that's expected.

**Files:**
- Modify: `backend/tests/test_agent.py`

- [ ] **Step 1: Replace test_agent.py**

Replace the entire file content with:

```python
import json
import pytest
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def test_run_query_returns_dict_with_answer_and_sources():
    from agent import run_query

    state = {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Sigma Oasis opened 7 shows."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("What was the most common opener in 2024?")

    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)


def test_run_query_answer_text_matches_final_ai_message():
    from agent import run_query

    state = {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Sigma Oasis opened 7 shows."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("What was the most common opener in 2024?")

    assert result["answer"] == "Sigma Oasis opened 7 shows."


def test_run_query_extracts_source_from_tool_message():
    from agent import run_query

    tool_result = {"total": 1, "results": [], "source": "setlist.fm"}
    ai_with_call = AIMessage(
        content="",
        tool_calls=[{"name": "search_setlists", "args": {}, "id": "call_1", "type": "tool_call"}],
    )
    state = {
        "messages": [
            HumanMessage(content="test"),
            ai_with_call,
            ToolMessage(content=json.dumps(tool_result), name="search_setlists", tool_call_id="call_1"),
            AIMessage(content="Sigma Oasis opened 7 shows in 2024."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("What was the most common opener in 2024?")

    assert "Sigma Oasis" in result["answer"]
    assert "setlist.fm" in result["sources"]


def test_run_query_deduplicates_sources():
    from agent import run_query

    tool_result = {"total": 0, "results": [], "source": "setlist.fm"}
    ai_with_call = AIMessage(
        content="",
        tool_calls=[{"name": "search_setlists", "args": {}, "id": "call_1", "type": "tool_call"}],
    )
    state = {
        "messages": [
            HumanMessage(content="test"),
            ai_with_call,
            ToolMessage(content=json.dumps(tool_result), name="search_setlists", tool_call_id="call_1"),
            AIMessage(content="No results."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("anything")

    assert result["sources"].count("setlist.fm") == 1


def test_run_query_prepends_history_as_langchain_messages():
    from agent import run_query

    history = [
        {"role": "user", "content": "when was tweezer last played?"},
        {"role": "assistant", "content": "Tweezer was last played on December 31, 2025."},
    ]
    state = {"messages": [AIMessage(content="Carini was played recently.")]}
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        run_query("what about carini?", history=history)

    call_messages = mock_app.invoke.call_args[0][0]["messages"]
    assert isinstance(call_messages[0], HumanMessage)
    assert call_messages[0].content == "when was tweezer last played?"
    assert isinstance(call_messages[1], AIMessage)
    assert call_messages[1].content == "Tweezer was last played on December 31, 2025."
    assert isinstance(call_messages[2], HumanMessage)
    assert call_messages[2].content == "what about carini?"


def test_run_query_empty_history_sends_single_user_message():
    from agent import run_query

    state = {"messages": [AIMessage(content="Some answer.")]}
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        run_query("what opened the show?")

    call_messages = mock_app.invoke.call_args[0][0]["messages"]
    assert len(call_messages) == 1
    assert isinstance(call_messages[0], HumanMessage)
    assert call_messages[0].content == "what opened the show?"


def test_graph_has_agent_and_tools_nodes():
    import agent
    assert "agent" in agent._app.nodes
    assert "tools" in agent._app.nodes


def test_local_tools_list_contains_all_six_tools():
    import agent
    tool_names = [t.name for t in agent.LOCAL_TOOLS]
    assert "search_setlists" in tool_names
    assert "get_jamcharts" in tool_names
    assert "get_song_history" in tool_names
    assert "search_shows" in tool_names
    assert "search_discography" in tool_names
    assert "get_song_stats" in tool_names


def test_web_search_tool_config_is_correct_type():
    import agent
    assert agent.WEB_SEARCH_TOOL["type"] == "web_search_20250305"
    assert agent.WEB_SEARCH_TOOL["name"] == "web_search"


def test_run_query_detects_web_search_source_from_tool_calls():
    from agent import run_query

    ai_with_web = AIMessage(
        content="",
        tool_calls=[{"name": "web_search", "args": {}, "id": "call_web", "type": "tool_call"}],
    )
    final_ai = AIMessage(content="Phish announced a 2026 summer tour.")
    state = {
        "messages": [
            HumanMessage(content="Any tour news?"),
            ai_with_web,
            final_ai,
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("Any Phish tour news?")

    assert "web" in result["sources"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_agent.py -v
```

Expected: multiple failures — `ImportError` or `AttributeError` because `agent._app`, `agent.LOCAL_TOOLS`, `agent.WEB_SEARCH_TOOL` don't exist yet on the old agent.

---

## Task 7: Implement agent.py with LangGraph

**Files:**
- Modify: `backend/agent.py`

- [ ] **Step 1: Replace agent.py**

Replace the entire file content with:

```python
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from tools.setlistfm import search_setlists
from tools.phishnet import get_jamcharts, get_song_history, search_shows
from tools.discography import search_discography
from tools.ihoz import get_song_stats

LOCAL_TOOLS = [
    search_setlists,
    get_jamcharts,
    get_song_history,
    search_shows,
    search_discography,
    get_song_stats,
]

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 3}

SYSTEM_PROMPT = (
    "You are PhishBot, an expert on Phish's concert history. "
    "You have seven tools — use the most appropriate one:\n"
    "- search_setlists: full setlist for a specific show date (YYYY-MM-DD), when/where a song was played, openers/closers\n"
    "- get_jamcharts: best or longest versions of a song, notable jams, must-hear performances\n"
    "- get_song_history: a song's origins, story, background, or lyrics\n"
    "- search_shows: shows by state or venue (e.g. 'shows in Minnesota', 'all MSG shows')\n"
    "- search_discography: which album a song is from, album tracklists, release years\n"
    "- get_song_stats: gap tracking, set distribution (Set 1 vs Set 2 tendency), "
    "song transitions (what usually comes before/after a song) — sourced from ihoz.com, "
    "but ihoz.com lags behind recent shows by weeks or months; always caveat 'last played' answers "
    "with 'as of ihoz.com data' and suggest the user verify for very recent shows\n"
    "- web_search: tour announcements, recent news, ticket info, anything not covered by the other tools\n"
    "Be specific: cite dates, venues, durations, and counts when you have them. "
    "Use markdown formatting freely — tables, bold, bullet points. Do not use emojis."
)

_llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=1024)
_model = _llm.bind_tools(LOCAL_TOOLS + [WEB_SEARCH_TOOL])


def _agent(state: MessagesState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = _model.invoke(messages)
    return {"messages": [response]}


_tool_node = ToolNode(LOCAL_TOOLS)

_graph = StateGraph(MessagesState)
_graph.add_node("agent", _agent)
_graph.add_node("tools", _tool_node)
_graph.add_edge(START, "agent")
_graph.add_conditional_edges("agent", tools_condition)
_graph.add_edge("tools", "agent")

_app = _graph.compile()


def run_query(question: str, history: list[dict] | None = None) -> dict:
    messages = []
    for msg in (history or []):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=question))

    result = _app.invoke({"messages": messages})
    final_messages = result["messages"]

    answer = "No answer generated."
    sources = set()

    for msg in final_messages:
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                if "source" in data:
                    sources.add(data["source"])
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(msg, AIMessage):
            for tc in getattr(msg, "tool_calls", []):
                if tc.get("name") == "web_search":
                    sources.add("web")
            if not getattr(msg, "tool_calls", []) and isinstance(msg.content, str) and msg.content:
                answer = msg.content

    return {"answer": answer, "sources": list(sources)}
```

> **Note on web_search + bind_tools:** `bind_tools` may not pass the raw Anthropic `web_search` dict through correctly — it expects tools with `name`/`description`/`input_schema`. If the server returns an error about the web_search tool format, remove `WEB_SEARCH_TOOL` from the `bind_tools` call and instead pass it via `model_kwargs`:
> ```python
> _llm = ChatAnthropic(
>     model="claude-sonnet-4-6",
>     max_tokens=1024,
>     model_kwargs={"tools": [WEB_SEARCH_TOOL]},
> )
> _model = _llm.bind_tools(LOCAL_TOOLS)
> ```

- [ ] **Step 2: Run the new agent tests**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_agent.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend/agent.py
git commit -m "feat: replace while-True loop with LangGraph StateGraph"
```

---

## Task 8: Full test suite and final verification

**Files:** None

- [ ] **Step 1: Run the complete test suite**

```bash
cd backend && source .venv/bin/activate && pytest tests/ -v
```

Expected: all tests pass across `test_agent.py`, `test_phishnet.py`, `test_setlistfm.py`, `test_ihoz.py`, `test_discography.py`, and `test_main.py`.

- [ ] **Step 2: Verify the server starts cleanly**

```bash
cd backend && source .venv/bin/activate && uvicorn main:app --reload &
sleep 3
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What album is Sigma Oasis on?", "history": []}' | python -m json.tool
kill %1
```

Expected: JSON response with `answer` (mentioning Sigma Oasis) and `sources` list. No traceback.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete LangGraph port — @tool decorators + StateGraph agent"
```
