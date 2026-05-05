# Discography Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hard-coded Phish discography tool so Claude can answer "which album is Carini from?", "what's on Farmhouse?", and "when did Big Boat come out?" without hitting any external API.

**Architecture:** A new `backend/tools/discography.py` file holds the complete studio discography as a Python list of dicts plus `SEARCH_DISCOGRAPHY_TOOL` and `search_discography()`. No network calls — pure in-memory lookup. Song and album searches use case-insensitive partial matching so "number line" finds "Backwards Down the Number Line". The tool is then registered as the fifth tool in `agent.py`.

**Tech Stack:** Python 3.11+, no external dependencies

---

## File Map

**Create:**
- `backend/tools/discography.py` — `DISCOGRAPHY` data, `SEARCH_DISCOGRAPHY_TOOL` dict, `search_discography()`
- `backend/tests/test_discography.py` — unit tests

**Modify:**
- `backend/agent.py` — import and register fifth tool, update system prompt

---

### Task 1: discography.py tool

**Files:**
- Create: `backend/tools/discography.py`
- Create: `backend/tests/test_discography.py`

- [ ] **Step 1: Write the failing tests**

Write to `backend/tests/test_discography.py`:

```python
def test_tool_definition_shape():
    from tools.discography import SEARCH_DISCOGRAPHY_TOOL

    assert SEARCH_DISCOGRAPHY_TOOL["name"] == "search_discography"
    assert "description" in SEARCH_DISCOGRAPHY_TOOL
    props = SEARCH_DISCOGRAPHY_TOOL["input_schema"]["properties"]
    assert "song" in props
    assert "album" in props


def test_song_lookup_finds_correct_album():
    from tools.discography import search_discography

    result = search_discography(song="Kill Devil Falls")
    assert len(result["matches"]) == 1
    assert result["matches"][0]["album"] == "Joy"
    assert result["matches"][0]["year"] == 2009


def test_song_lookup_is_case_insensitive():
    from tools.discography import search_discography

    result = search_discography(song="kill devil falls")
    assert len(result["matches"]) == 1
    assert result["matches"][0]["album"] == "Joy"


def test_song_lookup_partial_match():
    from tools.discography import search_discography

    result = search_discography(song="Number Line")
    assert any("Backwards Down the Number Line" in m["song"] for m in result["matches"])


def test_song_lookup_not_found_returns_empty():
    from tools.discography import search_discography

    result = search_discography(song="Nonexistent Song XYZ")
    assert result["matches"] == []
    assert result["source"] == "discography"


def test_album_lookup_returns_year_and_tracklist():
    from tools.discography import search_discography

    result = search_discography(album="Rift")
    assert len(result["albums"]) == 1
    album = result["albums"][0]
    assert album["year"] == 1993
    assert "Maze" in album["songs"]
    assert "Horn" in album["songs"]


def test_album_lookup_is_case_insensitive():
    from tools.discography import search_discography

    result = search_discography(album="farmhouse")
    assert len(result["albums"]) == 1
    assert result["albums"][0]["title"] == "Farmhouse"


def test_album_lookup_partial_match():
    from tools.discography import search_discography

    result = search_discography(album="Picture of Nectar")
    assert len(result["albums"]) == 1
    assert result["albums"][0]["year"] == 1992


def test_album_lookup_not_found_returns_empty():
    from tools.discography import search_discography

    result = search_discography(album="Nonexistent Album XYZ")
    assert result["albums"] == []
    assert result["source"] == "discography"


def test_no_params_returns_all_albums():
    from tools.discography import search_discography

    result = search_discography()
    assert len(result["albums"]) >= 10
    titles = [a["title"] for a in result["albums"]]
    assert "Junta" in titles
    assert "Joy" in titles
    assert "Sigma Oasis" in titles


def test_returns_source():
    from tools.discography import search_discography

    assert search_discography(song="Maze")["source"] == "discography"
    assert search_discography(album="Rift")["source"] == "discography"
    assert search_discography()["source"] == "discography"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_discography.py -v
```

Expected: `ModuleNotFoundError: No module named 'tools.discography'`

- [ ] **Step 3: Implement discography.py**

Write to `backend/tools/discography.py`:

```python
from typing import Optional

DISCOGRAPHY = [
    {
        "title": "The White Tape",
        "year": 1984,
        "label": "Self-released (officially released 1999 via Phish.com)",
        "notes": "Early rehearsal cassette, circulated as a bootleg for years before official release.",
        "songs": [
            "Camel Walk", "Fuck Your Face", "Halley's Comet", "Slave to the Traffic Light",
            "Standin' on the Corner", "Scissor Man", "Sneaking Sally Through the Alley",
            "Dog Log", "Letter to Jimmy Page", "Skippy the Wondermouse",
            "Flat Fee", "Swing Low Sweet Chariot",
        ],
    },
    {
        "title": "Junta",
        "year": 1989,
        "label": "Absolute A-Go-Go Records (reissued 1992)",
        "notes": "Self-released debut. Remastered and reissued commercially in 1992.",
        "songs": [
            "Fee", "You Enjoy Myself", "Fluffhead", "The Sloth", "Golgi Apparatus",
            "Foam", "Dinner and a Movie", "Divided Sky", "David Bowie", "Bike",
            "Union Federal", "Sanity", "Icculus",
        ],
    },
    {
        "title": "A Picture of Nectar",
        "year": 1992,
        "label": "Elektra",
        "songs": [
            "Llama", "Eliza", "Cavern", "Poor Heart", "Stash", "Manteca",
            "Guelah Papyrus", "Magilla", "The Landlady", "Glide", "Tweezer",
            "The Mango Song", "Chalk Dust Torture", "Faht", "Catapult", "Tweezer Reprise",
        ],
    },
    {
        "title": "Rift",
        "year": 1993,
        "label": "Elektra",
        "notes": "Concept album structured around a dream sequence.",
        "songs": [
            "Rift", "Fast Enough for You", "Lengthwise", "Maze", "Sparkle", "Horn",
            "The Wedge", "My Friend My Friend", "Weigh", "All Things Reconsidered",
            "Mound", "It's Ice", "The Horse", "Silent in the Morning",
        ],
    },
    {
        "title": "Hoist",
        "year": 1994,
        "label": "Elektra",
        "songs": [
            "Julius", "Down with Disease", "Why Don't We Do It in the Road?",
            "Riker's Mailbox", "Axilla (Part II)", "Lifeboy", "Sample in a Jar",
            "Demand", "If I Could", "Reba", "Wolfman's Brother", "Scent of a Mule",
            "Dog Faced Boy", "Keyboard Cavalry",
        ],
    },
    {
        "title": "Billy Breathes",
        "year": 1996,
        "label": "Elektra",
        "songs": [
            "Free", "Character Zero", "Waste", "Taste", "Cars Trucks Buses", "Talk",
            "Theme from the Bottom", "Train Song", "Bliss", "Billy Breathes",
            "Swept Away", "Steep", "Prince Caspian",
        ],
    },
    {
        "title": "The Story of the Ghost",
        "year": 1998,
        "label": "Elektra",
        "songs": [
            "Ghost", "Birds of a Feather", "Meat", "Guyute", "Fikus", "Shafty",
            "Limb by Limb", "Frankie Says", "Water in the Sky", "Roggae", "Mozambique",
            "The Inlaw Josie Wales", "Vultures", "Sleep", "Stay (Faraway, So Close!)",
        ],
    },
    {
        "title": "Farmhouse",
        "year": 2000,
        "label": "Elektra",
        "songs": [
            "Farmhouse", "Twist", "Bug", "Back on the Train", "Heavy Things",
            "Dirt", "Piper", "Sleep Again", "Sand", "First Tube",
        ],
    },
    {
        "title": "Round Room",
        "year": 2002,
        "label": "Elektra",
        "notes": "Recorded live-to-tape in the studio over five days.",
        "songs": [
            "Pebbles and Marbles", "Anything But Me", "Round Room", "Walls of the Cave",
            "Seven Below", "Waves", "Friday", "Mock Song", "Thunderhead",
            "All of These Dreams", "Plasma", "46 Days",
        ],
    },
    {
        "title": "Undermind",
        "year": 2004,
        "label": "Elektra / Rhino",
        "songs": [
            "Nothing", "Secret Smile", "Crowd Control", "Army of One", "Magnet",
            "Scabbard", "Air Safari", "A Song I Heard the Ocean Sing",
            "Two Versions of Me", "The Connection", "Access Me", "Inside Out",
        ],
    },
    {
        "title": "Joy",
        "year": 2009,
        "label": "JEMP Records",
        "notes": "First album after the 2004-2009 hiatus.",
        "songs": [
            "Backwards Down the Number Line", "Stealing Time from the Faulty Plan",
            "Sugar Shack", "Light", "Kill Devil Falls", "I Been Around", "Ocelot",
            "Time Turns Elastic", "Twenty Years Later", "Joy", "Alaska",
        ],
    },
    {
        "title": "Fuego",
        "year": 2014,
        "label": "JEMP Records",
        "songs": [
            "Fuego", "The Line", "Halfway to the Moon", "Devotion to a Dream",
            "Waiting All Night", "Wombat", "Winterqueen", "Sing Monica", "555", "Wingsuit",
        ],
    },
    {
        "title": "Big Boat",
        "year": 2016,
        "label": "JEMP Records",
        "songs": [
            "Friends", "Breath and Burning", "Things People Do", "Blaze On",
            "Tide Turns", "Miss You", "Petrichor", "Running Man", "More",
            "I Always Wanted It This Way", "Havana Affair", "Home",
        ],
    },
    {
        "title": "Kasvot Växt: i rokk",
        "year": 2018,
        "label": "JEMP Records",
        "notes": (
            "Released as Phish's Halloween 2018 musical costume, presented as recordings "
            "from an obscure Scandinavian prog-rock band 'Kasvot Växt'. "
            "The songs are original Phish compositions. Many also appear on Sigma Oasis."
        ),
        "songs": [
            "Mercury", "Lonely Trip", "Leaves", "Thread", "Drift While Sleeping",
            "Mull", "When Circus Comes", "Everything's Right", "Evolve",
            "Abstract", "Passing Through",
        ],
    },
    {
        "title": "Sigma Oasis",
        "year": 2020,
        "label": "JEMP Records",
        "notes": "Released during the COVID-19 pandemic. Studio versions of songs previewed at Halloween 2018.",
        "songs": [
            "Everything's Right", "No Men in No Man's Land", "Mercury", "Thread",
            "Leaves", "Sigma Oasis", "Steam", "Lonely Trip", "Evolve",
            "Light Much Brighter", "Turtle in the Clouds",
        ],
    },
]

SEARCH_DISCOGRAPHY_TOOL = {
    "name": "search_discography",
    "description": (
        "Look up Phish studio albums and song origins. "
        "Use 'song' to find which album a song appears on. "
        "Use 'album' to get the tracklist and release year for an album. "
        "Call with no parameters to list all studio albums. "
        "Covers all studio releases from The White Tape (1984) through Sigma Oasis (2020)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Song name to look up, e.g. 'Carini', 'Maze', 'First Tube'",
            },
            "album": {
                "type": "string",
                "description": "Album name to look up, e.g. 'Rift', 'Farmhouse', 'Joy'",
            },
        },
        "required": [],
    },
}


def search_discography(
    song: Optional[str] = None,
    album: Optional[str] = None,
) -> dict:
    if song:
        query = song.lower()
        matches = []
        for record in DISCOGRAPHY:
            for track in record["songs"]:
                if query in track.lower():
                    matches.append({
                        "song": track,
                        "album": record["title"],
                        "year": record["year"],
                    })
        return {"matches": matches, "source": "discography"}

    if album:
        query = album.lower()
        albums = [r for r in DISCOGRAPHY if query in r["title"].lower()]
        return {"albums": albums, "source": "discography"}

    # No params — return index of all albums
    index = [{"title": r["title"], "year": r["year"]} for r in DISCOGRAPHY]
    return {"albums": index, "source": "discography"}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_discography.py -v
```

Expected: all 11 tests pass.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass (45 existing + 11 new = 56 total).

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/tools/discography.py backend/tests/test_discography.py
git commit -m "feat: add hard-coded Phish discography tool"
```

---

### Task 2: Wire discography into the agent

**Files:**
- Modify: `backend/agent.py`
- Modify: `backend/tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_agent.py`:

```python
def test_agent_dispatch_includes_search_discography():
    import agent
    assert "search_discography" in agent.TOOL_DISPATCH
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_agent.py::test_agent_dispatch_includes_search_discography -v
```

Expected: FAIL — `search_discography` not yet in `TOOL_DISPATCH`.

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
from tools.discography import SEARCH_DISCOGRAPHY_TOOL, search_discography

client = anthropic.Anthropic()

TOOL_DISPATCH = {
    "search_setlists": search_setlists,
    "get_jamcharts": get_jamcharts,
    "get_song_history": get_song_history,
    "search_shows": search_shows,
    "search_discography": search_discography,
}

SYSTEM_PROMPT = (
    "You are PhishBot, an expert on Phish's concert history. "
    "You have five tools — use the most appropriate one:\n"
    "- search_setlists: when/where was a song played, show openers/closers, setlist queries\n"
    "- get_jamcharts: best or longest versions of a song, notable jams, must-hear performances\n"
    "- get_song_history: a song's origins, story, background, or lyrics\n"
    "- search_shows: shows by state or venue (e.g. 'shows in Minnesota', 'all MSG shows')\n"
    "- search_discography: which album a song is from, album tracklists, release years\n"
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
            tools=[SETLISTFM_TOOL, JAMCHARTS_TOOL, SONG_HISTORY_TOOL, SEARCH_SHOWS_TOOL, SEARCH_DISCOGRAPHY_TOOL],
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

Expected: all tests pass (56 existing + 1 new = 57 total).

- [ ] **Step 5: Smoke test**

Terminal 1:
```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
uvicorn main:app --reload
```

Terminal 2 — test song-to-album lookup:
```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What album is Carini from?"}' | python3 -m json.tool
```

Expected: answer says Joy (2009). `"sources"` includes `"discography"`.

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What songs are on Farmhouse?"}' | python3 -m json.tool
```

Expected: lists Farmhouse tracklist including First Tube, Sand, Twist etc.

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about the White Tape"}' | python3 -m json.tool
```

Expected: mentions 1984, bootleg history, officially released 1999.

Stop server with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/agent.py backend/tests/test_agent.py
git commit -m "feat: wire discography into agent, expand to five tools"
```

---

## Done

PhishBot now answers five classes of questions:
- **"When/where was X played"** → `search_setlists`
- **"Best/longest version of X"** → `get_jamcharts`
- **"History/story of X"** → `get_song_history`
- **"Shows in [state/venue]"** → `search_shows`
- **"Which album / what's on [album]"** → `search_discography`

**Data note:** The discography data covers studio albums through Sigma Oasis (2020). Tracklists for Kasvot Växt and Sigma Oasis may have some overlap — both albums share several songs (Mercury, Leaves, Thread, etc.) as the studio recordings were released after the Halloween 2018 debut. If any song or album details are wrong, edit `DISCOGRAPHY` in `backend/tools/discography.py` directly.
