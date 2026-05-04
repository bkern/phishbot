# phish.net Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a phish.net API tool that gives Claude access to jam charts (notable jams with durations) and song history, then wire it into the agent alongside the existing setlist.fm tool.

**Architecture:** Two new Claude tool definitions live in `backend/tools/phishnet.py` — `get_jamcharts` (notable jams with track times from community jam charts) and `get_song_history` (song background, history notes, metadata). `agent.py` is updated to pass all three tools to Claude and route tool calls to the right implementation. With three tools, Claude naturally picks the right one based on question type: setlist.fm for "when/where" questions, phish.net jamcharts for "best/longest jam" questions, phish.net song history for "tell me about this song" questions.

**Tech Stack:** Python 3.11+, httpx, phish.net API v5 (`https://api.phish.net/v5/`), Anthropic SDK (already wired)

---

## File Map

**Create:**
- `backend/tools/phishnet.py` — `JAMCHARTS_TOOL` dict, `SONG_HISTORY_TOOL` dict, `_song_to_slug()` helper, `get_jamcharts()`, `get_song_history()`
- `backend/tests/test_phishnet.py` — unit tests for both functions

**Modify:**
- `backend/conftest.py` — add `PHISHNET_API_KEY=test-key`
- `backend/.env.example` — add `PHISHNET_API_KEY=your-phishnet-key-here`
- `backend/agent.py` — import new tools, expand `TOOL_DISPATCH`, update `tools=` list, update `SYSTEM_PROMPT`

---

### Task 1: phishnet.py tool

**Files:**
- Create: `backend/tools/phishnet.py`
- Create: `backend/tests/test_phishnet.py`
- Modify: `backend/conftest.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Update conftest.py**

Write to `backend/conftest.py`:
```python
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("SETLISTFM_API_KEY", "test-key")
os.environ.setdefault("PHISHNET_API_KEY", "test-key")
```

- [ ] **Step 2: Update .env.example**

Write to `backend/.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-...
SETLISTFM_API_KEY=your-setlistfm-key-here
PHISHNET_API_KEY=your-phishnet-key-here
```

- [ ] **Step 3: Write the failing tests**

Write to `backend/tests/test_phishnet.py`:
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


def test_jamcharts_tool_definition_shape():
    from tools.phishnet import JAMCHARTS_TOOL

    assert JAMCHARTS_TOOL["name"] == "get_jamcharts"
    assert "description" in JAMCHARTS_TOOL
    assert "input_schema" in JAMCHARTS_TOOL
    props = JAMCHARTS_TOOL["input_schema"]["properties"]
    assert "song" in props
    assert JAMCHARTS_TOOL["input_schema"]["required"] == ["song"]


def test_song_history_tool_definition_shape():
    from tools.phishnet import SONG_HISTORY_TOOL

    assert SONG_HISTORY_TOOL["name"] == "get_song_history"
    assert "description" in SONG_HISTORY_TOOL
    props = SONG_HISTORY_TOOL["input_schema"]["properties"]
    assert "song" in props
    assert SONG_HISTORY_TOOL["input_schema"]["required"] == ["song"]


def test_song_to_slug_simple():
    from tools.phishnet import _song_to_slug

    assert _song_to_slug("Tweezer") == "tweezer"


def test_song_to_slug_multi_word():
    from tools.phishnet import _song_to_slug

    assert _song_to_slug("Bathtub Gin") == "bathtub-gin"
    assert _song_to_slug("You Enjoy Myself") == "you-enjoy-myself"
    assert _song_to_slug("Chalk Dust Torture") == "chalk-dust-torture"


def test_get_jamcharts_returns_source():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert result["source"] == "phish.net"


def test_get_jamcharts_returns_jams_with_date_venue_duration():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    jam = result["jams"][0]
    assert jam["date"] == "1994-07-08"
    assert "Great Woods" in jam["venue"]
    assert jam["duration"] == "38:23"


def test_get_jamcharts_includes_notes_when_present():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert result["jams"][0]["notes"] == "Epic segue into Lifeboy"


def test_get_jamcharts_omits_notes_when_empty():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert "notes" not in result["jams"][1]


def test_get_jamcharts_passes_slug_to_api():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])) as mock_get:
        get_jamcharts(song="Bathtub Gin")
    url = mock_get.call_args[0][0]
    assert "bathtub-gin" in url


def test_get_song_history_returns_source():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SONGDATA)):
        result = get_song_history(song="Tweezer")
    assert result["source"] == "phish.net"


def test_get_song_history_returns_name_and_history():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SONGDATA)):
        result = get_song_history(song="Tweezer")
    assert result["song"] == "Tweezer"
    assert "1990" in result["history"]


def test_get_song_history_returns_not_found_when_empty():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = get_song_history(song="Nonexistent XYZ")
    assert result["song"] is None
    assert result["history"] is None
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_phishnet.py -v
```

Expected: `ImportError: cannot import name 'JAMCHARTS_TOOL' from 'tools.phishnet'` or `ModuleNotFoundError`.

- [ ] **Step 5: Implement phishnet.py**

Write to `backend/tools/phishnet.py`:
```python
import os
import re
import httpx

PHISHNET_BASE = "https://api.phish.net/v5"

JAMCHARTS_TOOL = {
    "name": "get_jamcharts",
    "description": (
        "Get community jam charts for a Phish song — the notable, highly-rated performances "
        "with track durations. Use this for questions about the best or longest versions of a song, "
        "or when asked about must-hear jams. Returns each jam's date, venue, set, duration, and notes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Song name, e.g. 'Tweezer', 'Bathtub Gin', 'Carini'",
            },
        },
        "required": ["song"],
    },
}

SONG_HISTORY_TOOL = {
    "name": "get_song_history",
    "description": (
        "Get the history, background, and metadata for a Phish song from phish.net's "
        "editorial database. Use this for questions about a song's origins, meaning, or story."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Song name, e.g. 'You Enjoy Myself', 'Wilson', 'Harry Hood'",
            },
        },
        "required": ["song"],
    },
}


def _song_to_slug(song: str) -> str:
    slug = song.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def get_jamcharts(song: str) -> dict:
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

    return {"song": song, "jams": jams, "source": "phish.net"}


def get_song_history(song: str) -> dict:
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
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_phishnet.py -v
```

Expected: all 12 tests pass.

- [ ] **Step 7: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/tools/phishnet.py backend/tests/test_phishnet.py \
    backend/conftest.py backend/.env.example
git commit -m "feat: add phish.net jamcharts and song history tools with tests"
```

---

### Task 2: Wire phish.net tools into the agent

**Files:**
- Modify: `backend/agent.py`

- [ ] **Step 1: Write the failing test**

Add this test to `backend/tests/test_agent.py` (append at the bottom):

```python
def test_agent_dispatch_includes_phishnet_tools():
    import agent
    assert "get_jamcharts" in agent.TOOL_DISPATCH
    assert "get_song_history" in agent.TOOL_DISPATCH
    assert "search_setlists" in agent.TOOL_DISPATCH
```

- [ ] **Step 2: Run the new test to verify it fails**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_agent.py::test_agent_dispatch_includes_phishnet_tools -v
```

Expected: FAIL with `AssertionError` — `get_jamcharts` is not yet in `TOOL_DISPATCH`.

- [ ] **Step 3: Update agent.py**

Write to `backend/agent.py`:
```python
import json
import anthropic
from tools.setlistfm import TOOL_DEFINITION as SETLISTFM_TOOL, search_setlists
from tools.phishnet import JAMCHARTS_TOOL, SONG_HISTORY_TOOL, get_jamcharts, get_song_history

client = anthropic.Anthropic()

TOOL_DISPATCH = {
    "search_setlists": search_setlists,
    "get_jamcharts": get_jamcharts,
    "get_song_history": get_song_history,
}

SYSTEM_PROMPT = (
    "You are PhishBot, an expert on Phish's concert history. "
    "You have three tools — use the most appropriate one:\n"
    "- search_setlists: when/where was a song played, show openers/closers, setlist queries\n"
    "- get_jamcharts: best or longest versions of a song, notable jams, must-hear performances\n"
    "- get_song_history: a song's origins, story, background, or lyrics\n"
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
            tools=[SETLISTFM_TOOL, JAMCHARTS_TOOL, SONG_HISTORY_TOOL],
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = TOOL_DISPATCH[block.name](**block.input)
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

- [ ] **Step 4: Run the full backend test suite**

```bash
pytest tests/ -v
```

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass. If any fail, the most likely cause is an import error in `phishnet.py` — read the traceback carefully.

- [ ] **Step 5: Add your PHISHNET_API_KEY to .env**

```bash
# Open backend/.env and add your real phish.net API key:
# PHISHNET_API_KEY=your-actual-key-here
```

- [ ] **Step 6: Smoke-test with the real API**

Start the backend:
```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
uvicorn main:app --reload
```

In another terminal, try a question that exercises the new tools:
```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the most notable Tweezer jams ever played?"}' | python3 -m json.tool
```

Expected: answer mentions specific dates, venues, and durations from the phish.net jam charts. `sources` should include `"phish.net"`.

Try a second query that uses both tools:
```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about the history of You Enjoy Myself"}' | python3 -m json.tool
```

Expected: Claude uses `get_song_history` and returns background about YEM.

Stop the server with Ctrl+C.

- [ ] **Step 7: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/agent.py backend/tests/test_agent.py
git commit -m "feat: wire phish.net tools into agent, update system prompt"
```

---

## Done

At this point PhishBot answers three classes of questions:
- **"When/where"** → setlist.fm (`search_setlists`)
- **"Best/longest jam"** → phish.net jamcharts (`get_jamcharts`)
- **"History/story"** → phish.net song data (`get_song_history`)

**Note on slug misses:** The slug derivation (`"Bathtub Gin"` → `"bathtub-gin"`) works for most songs but will 404 for songs whose phish.net slug differs from the naive lowercase-and-hyphenate conversion. If a query fails with a 404, the agent will receive an error and tell the user gracefully. A song-name-to-slug lookup endpoint could be added later.

**Next step:** LangGraph orchestration and ihoz.com stats scraper (Phase 2).
