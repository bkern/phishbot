# search_shows Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `search_shows` tool to phish.net's tool module so Claude can answer questions about shows by state ("how many shows in Minnesota?") or by venue ("all shows at Madison Square Garden").

**Architecture:** `search_shows(state, venue, year)` is added to `backend/tools/phishnet.py` following the exact same pattern as `get_jamcharts` and `get_song_history`. Venue queries require two sequential API calls: a venue name lookup to get a `venueid`, then a shows-by-venueid lookup. State queries hit one endpoint directly. Year is a client-side post-filter since the API doesn't support combined state+year filtering. The tool is then registered in `agent.py` alongside the existing three tools.

**Tech Stack:** Python 3.11+, httpx, urllib.parse, phish.net API v5, Anthropic SDK (already wired)

---

## File Map

**Modify:**
- `backend/tools/phishnet.py` — add `SEARCH_SHOWS_TOOL` dict and `search_shows()` function
- `backend/tests/test_phishnet.py` — add 9 tests for the new function
- `backend/agent.py` — import and register `search_shows`, add 4th bullet to system prompt

---

### Task 1: Add search_shows to phishnet.py

**Files:**
- Modify: `backend/tools/phishnet.py`
- Modify: `backend/tests/test_phishnet.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_phishnet.py`:

```python
# ── search_shows tests ────────────────────────────────────────────────────────

SAMPLE_SHOWS = [
    {
        "showdate": "2023-07-15",
        "venue": "Target Center",
        "city": "Minneapolis",
        "state": "MN",
        "country": "USA",
    },
    {
        "showdate": "2019-08-02",
        "venue": "Xcel Energy Center",
        "city": "Saint Paul",
        "state": "MN",
        "country": "USA",
    },
]

SAMPLE_VENUE = [
    {
        "venueid": "123",
        "venuename": "Madison Square Garden",
        "city": "New York",
        "state": "NY",
        "country": "USA",
    }
]


def test_search_shows_tool_definition_shape():
    from tools.phishnet import SEARCH_SHOWS_TOOL

    assert SEARCH_SHOWS_TOOL["name"] == "search_shows"
    assert "description" in SEARCH_SHOWS_TOOL
    assert "input_schema" in SEARCH_SHOWS_TOOL
    props = SEARCH_SHOWS_TOOL["input_schema"]["properties"]
    assert "state" in props
    assert "venue" in props
    assert "year" in props


def test_search_shows_by_state_returns_source():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN")
    assert result["source"] == "phish.net"


def test_search_shows_by_state_returns_shows_with_correct_fields():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN")
    show = result["shows"][0]
    assert show["date"] == "2023-07-15"
    assert show["venue"] == "Target Center"
    assert show["city"] == "Minneapolis"
    assert show["state"] == "MN"


def test_search_shows_by_state_passes_state_to_url():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])) as mock_get:
        search_shows(state="CO")
    url = mock_get.call_args[0][0]
    assert "CO" in url


def test_search_shows_returns_total_count():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN")
    assert result["total"] == 2


def test_search_shows_by_state_filters_by_year():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN", year="2023")
    assert result["total"] == 1
    assert result["shows"][0]["date"] == "2023-07-15"


def test_search_shows_by_venue_makes_two_api_calls():
    from tools.phishnet import search_shows

    venue_resp = _mock_response(SAMPLE_VENUE)
    shows_resp = _mock_response(SAMPLE_SHOWS[:1])

    with patch("tools.phishnet.httpx.get", side_effect=[venue_resp, shows_resp]) as mock_get:
        result = search_shows(venue="Madison Square Garden")

    assert mock_get.call_count == 2
    assert result["source"] == "phish.net"
    assert result["shows"][0]["date"] == "2023-07-15"


def test_search_shows_by_venue_uses_venueid_in_second_call():
    from tools.phishnet import search_shows

    venue_resp = _mock_response([{
        "venueid": "789",
        "venuename": "Sphere",
        "city": "Las Vegas",
        "state": "NV",
        "country": "USA",
    }])
    shows_resp = _mock_response([])

    with patch("tools.phishnet.httpx.get", side_effect=[venue_resp, shows_resp]) as mock_get:
        search_shows(venue="Sphere")

    second_url = mock_get.call_args_list[1][0][0]
    assert "789" in second_url


def test_search_shows_venue_not_found_returns_empty():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = search_shows(venue="Nonexistent Venue XYZ")

    assert result["shows"] == []
    assert result["total"] == 0
    assert result["source"] == "phish.net"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_phishnet.py -k "search_shows" -v
```

Expected: `ImportError: cannot import name 'SEARCH_SHOWS_TOOL'`

- [ ] **Step 3: Add SEARCH_SHOWS_TOOL and search_shows to phishnet.py**

First, add `from urllib.parse import quote as url_quote` to the import block at the top of `backend/tools/phishnet.py`. The imports section should become:

```python
import os
import re
from urllib.parse import quote as url_quote
import httpx
```

Then append the following after the existing `get_song_history` function:

```python
SEARCH_SHOWS_TOOL = {
    "name": "search_shows",
    "description": (
        "Search Phish shows by US state or venue name. "
        "Use for questions like 'how many shows in Minnesota', "
        "'what venues has Phish played in Colorado', or "
        "'all shows at Madison Square Garden'. "
        "Provide state (2-letter abbreviation) OR venue name — not both. "
        "Optionally filter by year."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "2-letter US state abbreviation, e.g. 'MN' for Minnesota, 'CO' for Colorado, 'NY' for New York",
            },
            "venue": {
                "type": "string",
                "description": "Venue name, e.g. 'Madison Square Garden', 'Sphere', 'Red Rocks Amphitheatre'",
            },
            "year": {
                "type": "string",
                "description": "4-digit year to filter results, e.g. '2024'",
            },
        },
        "required": [],
    },
}


def search_shows(
    state: str = None,
    venue: str = None,
    year: str = None,
) -> dict:
    apikey = os.environ["PHISHNET_API_KEY"]

    if venue:
        venue_response = httpx.get(
            f"{PHISHNET_BASE}/venues/venuename/{url_quote(venue)}.json",
            params={"apikey": apikey},
            timeout=10.0,
        )
        venue_response.raise_for_status()
        venues = venue_response.json().get("data", [])
        if not venues:
            return {"shows": [], "total": 0, "source": "phish.net"}
        venueid = venues[0]["venueid"]

        shows_response = httpx.get(
            f"{PHISHNET_BASE}/shows/venueid/{venueid}.json",
            params={"apikey": apikey},
            timeout=10.0,
        )
        shows_response.raise_for_status()
        all_shows = shows_response.json().get("data", [])

    elif state:
        shows_response = httpx.get(
            f"{PHISHNET_BASE}/shows/state/{state}.json",
            params={"apikey": apikey},
            timeout=10.0,
        )
        shows_response.raise_for_status()
        all_shows = shows_response.json().get("data", [])

    else:
        return {"shows": [], "total": 0, "source": "phish.net"}

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

- [ ] **Step 4: Run the new tests to verify they pass**

```bash
pytest tests/test_phishnet.py -k "search_shows" -v
```

Expected: all 9 new tests pass.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass (35 existing + 9 new = 44 total).

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/tools/phishnet.py backend/tests/test_phishnet.py
git commit -m "feat: add search_shows tool for state and venue queries"
```

---

### Task 2: Wire search_shows into the agent

**Files:**
- Modify: `backend/agent.py`
- Modify: `backend/tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_agent.py`:

```python
def test_agent_dispatch_includes_search_shows():
    import agent
    assert "search_shows" in agent.TOOL_DISPATCH
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_agent.py::test_agent_dispatch_includes_search_shows -v
```

Expected: FAIL with `AssertionError` — `search_shows` is not yet in `TOOL_DISPATCH`.

- [ ] **Step 3: Update agent.py**

Write to `backend/agent.py`:

```python
import json
import anthropic
from tools.setlistfm import TOOL_DEFINITION as SETLISTFM_TOOL, search_setlists
from tools.phishnet import (
    JAMCHARTS_TOOL, SONG_HISTORY_TOOL, SEARCH_SHOWS_TOOL,
    get_jamcharts, get_song_history, search_shows,
)

client = anthropic.Anthropic()

TOOL_DISPATCH = {
    "search_setlists": search_setlists,
    "get_jamcharts": get_jamcharts,
    "get_song_history": get_song_history,
    "search_shows": search_shows,
}

SYSTEM_PROMPT = (
    "You are PhishBot, an expert on Phish's concert history. "
    "You have four tools — use the most appropriate one:\n"
    "- search_setlists: when/where was a song played, show openers/closers, setlist queries\n"
    "- get_jamcharts: best or longest versions of a song, notable jams, must-hear performances\n"
    "- get_song_history: a song's origins, story, background, or lyrics\n"
    "- search_shows: shows by state or venue (e.g. 'shows in Minnesota', 'all MSG shows')\n"
    "Be specific: cite dates, venues, durations, and counts when you have them."
)


def run_query(question: str) -> dict:
    messages = [{"role": "user", "content": question}]
    sources = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[SETLISTFM_TOOL, JAMCHARTS_TOOL, SONG_HISTORY_TOOL, SEARCH_SHOWS_TOOL],
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_fn = TOOL_DISPATCH.get(block.name)
                    if tool_fn is None:
                        result = {"error": f"Unknown tool: {block.name}", "source": "agent"}
                    else:
                        result = tool_fn(**block.input)
                    sources.append(result.get("source", block.name))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            answer = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "No answer generated.",
            )
            return {"answer": answer, "sources": list(set(sources))}

        else:
            return {"answer": "Unexpected stop reason from Claude.", "sources": []}
```

- [ ] **Step 4: Run the full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass (44 existing + 1 new = 45 total).

- [ ] **Step 5: Smoke test**

Terminal 1:
```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
uvicorn main:app --reload
```

Terminal 2:
```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many shows has Phish played in Minnesota?"}' | python3 -m json.tool
```

Expected: answer cites a specific count and lists venues or show dates. `"sources"` includes `"phish.net"`.

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many times has Phish played Madison Square Garden?"}' | python3 -m json.tool
```

Expected: answer uses `search_shows` with venue lookup, returns MSG show count. Stop server with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/agent.py backend/tests/test_agent.py
git commit -m "feat: wire search_shows into agent, update system prompt to four tools"
```

---

## Done

PhishBot now answers four classes of questions:
- **"When/where was X played"** → `search_setlists`
- **"Best/longest version of X"** → `get_jamcharts`
- **"History/story of X"** → `get_song_history`
- **"Shows in [state] / shows at [venue]"** → `search_shows`
