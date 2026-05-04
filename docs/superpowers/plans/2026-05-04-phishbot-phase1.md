# PhishBot Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an end-to-end PhishBot: React/Vite/Tailwind frontend → FastAPI backend → Claude tool use → setlist.fm API, all running locally.

**Architecture:** FastAPI exposes `POST /query`. The agent in `agent.py` gives Claude a `search_setlists` tool backed by the setlist.fm API. Claude decides when to call it, processes the results, and returns a synthesized answer. The React frontend (dark mode, search+result layout) shows the query box and answer card.

**Tech Stack:** Python 3.11+, FastAPI, Anthropic SDK, httpx, python-dotenv, pytest / React 18, Vite, TypeScript, Tailwind CSS v3, Vitest, @testing-library/react

---

## File Map

**Backend (create):**
- `backend/conftest.py` — sets test env vars before any module is imported
- `backend/main.py` — FastAPI app: CORS, `POST /query`, Pydantic models
- `backend/agent.py` — Claude tool-use loop: question → answer + sources
- `backend/tools/__init__.py` — makes `tools/` a package
- `backend/tools/setlistfm.py` — `TOOL_DEFINITION` dict + `search_setlists()` function
- `backend/requirements.txt` — Python dependencies
- `backend/.env.example` — template for API keys
- `backend/tests/__init__.py` — makes `tests/` a package
- `backend/tests/test_setlistfm.py` — unit tests for `search_setlists()`
- `backend/tests/test_agent.py` — unit tests for `run_query()`
- `backend/tests/test_main.py` — integration tests for `POST /query`

**Frontend (create):**
- `frontend/src/App.tsx` — root component: state machine (idle/loading/result/error), fetch to `/query`
- `frontend/src/components/QueryInput.tsx` — textarea, example chips, submit button
- `frontend/src/components/QueryInput.test.tsx` — unit tests
- `frontend/src/components/ResultCard.tsx` — answer display, source tags, loading state
- `frontend/src/components/ResultCard.test.tsx` — unit tests
- `frontend/src/main.tsx` — React entry point
- `frontend/src/index.css` — Tailwind directives + shimmer keyframe
- `frontend/src/test-setup.ts` — @testing-library/jest-dom import
- `frontend/index.html` — HTML shell with Inter font
- `frontend/package.json` — dependencies (via `npm create vite`)
- `frontend/vite.config.ts` — Vite + Vitest config
- `frontend/tailwind.config.js` — Tailwind content paths

**Root:**
- `.gitignore` — excludes `.venv/`, `node_modules/`, `.env`, `.superpowers/`

---

### Task 1: Backend scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/conftest.py`
- Create: `backend/tools/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/bskern/Projects/phishbot
mkdir -p backend/tools backend/tests
touch backend/tools/__init__.py backend/tests/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

Write to `backend/requirements.txt`:
```
anthropic>=0.40.0
fastapi>=0.115.0
uvicorn>=0.32.0
httpx>=0.27.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 3: Create .env.example**

Write to `backend/.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-...
SETLISTFM_API_KEY=your-setlistfm-key-here
```

- [ ] **Step 4: Create conftest.py (sets env vars for all tests)**

Write to `backend/conftest.py`:
```python
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("SETLISTFM_API_KEY", "test-key")
```

This file runs before any test module is imported, so `agent.py`'s module-level `anthropic.Anthropic()` call sees a key and doesn't raise.

- [ ] **Step 5: Create virtual environment and install dependencies**

```bash
cd /Users/bskern/Projects/phishbot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 6: Copy .env.example and fill in real keys**

```bash
cp .env.example .env
# Open .env and add your real ANTHROPIC_API_KEY and SETLISTFM_API_KEY
```

- [ ] **Step 7: Create .gitignore at project root**

Write to `/Users/bskern/Projects/phishbot/.gitignore`:
```
# Python
backend/.venv/
backend/__pycache__/
backend/**/__pycache__/
backend/.env
*.pyc

# Node
frontend/node_modules/
frontend/dist/

# Misc
.DS_Store
.superpowers/
```

- [ ] **Step 8: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add .gitignore backend/
git commit -m "chore: scaffold backend structure and dependencies"
```

---

### Task 2: setlist.fm tool

**Files:**
- Create: `backend/tools/setlistfm.py`
- Create: `backend/tests/test_setlistfm.py`

- [ ] **Step 1: Write the failing tests**

Write to `backend/tests/test_setlistfm.py`:
```python
import pytest
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


def test_tool_definition_shape():
    from tools.setlistfm import TOOL_DEFINITION

    assert TOOL_DEFINITION["name"] == "search_setlists"
    assert "description" in TOOL_DEFINITION
    assert "input_schema" in TOOL_DEFINITION
    props = TOOL_DEFINITION["input_schema"]["properties"]
    assert "year" in props
    assert "song" in props
    assert "position" in props


def test_search_returns_source():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists()
    assert result["source"] == "setlist.fm"


def test_search_returns_date_and_venue():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists()
    assert result["results"][0]["date"] == "01-08-2024"
    assert "Merriweather" in result["results"][0]["venue"]


def test_search_by_song_filters_to_matching_songs():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(song="Tweezer")
    matched = [s["name"] for s in result["results"][0]["songs"]]
    assert "Tweezer" in matched
    assert "Sigma Oasis" not in matched


def test_search_opener_returns_first_non_encore_song():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(position="opener")
    songs = result["results"][0]["songs"]
    assert len(songs) == 1
    assert songs[0]["name"] == "Sigma Oasis"


def test_search_closer_returns_last_non_encore_song():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(position="closer")
    songs = result["results"][0]["songs"]
    assert len(songs) == 1
    assert songs[0]["name"] == "Chalk Dust Torture"


def test_search_passes_year_param_to_api():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([])) as mock_get:
        search_setlists(year="2024")
    assert mock_get.call_args[1]["params"]["year"] == "2024"


def test_empty_results():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([])):
        result = search_setlists(song="Nonexistent Song XYZ")
    assert result["results"] == []
    assert result["total"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_setlistfm.py -v
```

Expected: `ImportError: cannot import name 'TOOL_DEFINITION' from 'tools.setlistfm'` or `ModuleNotFoundError`.

- [ ] **Step 3: Implement setlistfm.py**

Write to `backend/tools/setlistfm.py`:
```python
import os
import httpx

SETLISTFM_BASE = "https://api.setlist.fm/rest/1.0"

TOOL_DEFINITION = {
    "name": "search_setlists",
    "description": (
        "Search Phish setlists by year, song name, or both. "
        "Returns matching shows with song details and set positions. "
        "Use 'position' to find show openers or closers."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "year": {
                "type": "string",
                "description": "4-digit year, e.g. '2024'",
            },
            "song": {
                "type": "string",
                "description": "Song name to search for, e.g. 'Tweezer', 'Maze'",
            },
            "position": {
                "type": "string",
                "enum": ["opener", "closer", "any"],
                "description": (
                    "'opener' = first song of the show (excluding encores), "
                    "'closer' = last song before encores, "
                    "'any' = no position filter."
                ),
            },
        },
        "required": [],
    },
}


def search_setlists(
    year: str = None,
    song: str = None,
    position: str = "any",
) -> dict:
    params = {"artistName": "Phish", "p": 1}
    if year:
        params["year"] = year
    if song:
        params["songName"] = song

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
        date = setlist.get("eventDate", "")
        venue_obj = setlist.get("venue", {})
        venue = f"{venue_obj.get('name', '')}, {venue_obj.get('city', {}).get('name', '')}"

        main_songs = []
        all_songs = []
        for set_data in setlist.get("sets", {}).get("set", []):
            is_encore = bool(set_data.get("encore", 0))
            for song_obj in set_data.get("song", []):
                entry = {"name": song_obj.get("name", ""), "encore": is_encore}
                all_songs.append(entry)
                if not is_encore:
                    main_songs.append(entry)

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

        results.append({"date": date, "venue": venue, "songs": candidates})

    return {"total": data.get("total", 0), "results": results, "source": "setlist.fm"}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_setlistfm.py -v
```

Expected: all 8 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/tools/setlistfm.py backend/tests/test_setlistfm.py
git commit -m "feat: add setlist.fm search tool with tests"
```

---

### Task 3: Agent (Claude tool-use loop)

**Files:**
- Create: `backend/agent.py`
- Create: `backend/tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Write to `backend/tests/test_agent.py`:
```python
import pytest
from unittest.mock import MagicMock, patch


def _text_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _tool_use_response(tool_name: str, tool_input: dict, tool_id: str = "tu_1") -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = tool_id
    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [block]
    return response


def test_run_query_returns_answer_and_sources():
    from agent import run_query

    with patch("agent.client") as mock_client:
        mock_client.messages.create.return_value = _text_response("Sigma Oasis opened 7 shows.")
        result = run_query("What was the most common opener in 2024?")

    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)


def test_run_query_answer_text_matches_claude_response():
    from agent import run_query

    with patch("agent.client") as mock_client:
        mock_client.messages.create.return_value = _text_response("Sigma Oasis opened 7 shows.")
        result = run_query("What was the most common opener in 2024?")

    assert result["answer"] == "Sigma Oasis opened 7 shows."


def test_run_query_calls_tool_and_feeds_result_back_to_claude():
    from agent import run_query

    fake_tool_result = {
        "total": 1,
        "results": [{"date": "01-08-2024", "venue": "Merriweather, Columbia", "songs": [{"name": "Sigma Oasis", "encore": False}]}],
        "source": "setlist.fm",
    }

    with patch("agent.client") as mock_client, \
         patch("agent.TOOL_DISPATCH", {"search_setlists": lambda **kw: fake_tool_result}):
        mock_client.messages.create.side_effect = [
            _tool_use_response("search_setlists", {"year": "2024", "position": "opener"}),
            _text_response("Sigma Oasis opened 7 shows in 2024."),
        ]
        result = run_query("What was the most common opener in 2024?")

    assert "Sigma Oasis" in result["answer"]
    assert "setlist.fm" in result["sources"]
    assert mock_client.messages.create.call_count == 2


def test_run_query_deduplicates_sources():
    from agent import run_query

    fake_tool_result = {"total": 0, "results": [], "source": "setlist.fm"}

    with patch("agent.client") as mock_client, \
         patch("agent.TOOL_DISPATCH", {"search_setlists": lambda **kw: fake_tool_result}):
        mock_client.messages.create.side_effect = [
            _tool_use_response("search_setlists", {"year": "2024"}),
            _text_response("No results found."),
        ]
        result = run_query("anything")

    assert result["sources"].count("setlist.fm") == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Implement agent.py**

Write to `backend/agent.py`:
```python
import json
import anthropic
from tools.setlistfm import TOOL_DEFINITION, search_setlists

client = anthropic.Anthropic()

TOOL_DISPATCH = {
    "search_setlists": search_setlists,
}

SYSTEM_PROMPT = (
    "You are PhishBot, an expert on Phish's concert history. "
    "Use the search_setlists tool to look up setlist data before answering. "
    "Be specific: cite dates, venues, and counts when you have them. "
    "If a question requires data you don't have access to (e.g. song durations, jam lengths), "
    "say so clearly — that data isn't in setlist.fm."
)


def run_query(question: str) -> dict:
    messages = [{"role": "user", "content": question}]
    sources = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[TOOL_DEFINITION],
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

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/agent.py backend/tests/test_agent.py
git commit -m "feat: add Claude tool-use agent with tests"
```

---

### Task 4: FastAPI endpoint

**Files:**
- Create: `backend/main.py`
- Create: `backend/tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

Write to `backend/tests/test_main.py`:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_query_returns_200(client):
    with patch("main.run_query", return_value={"answer": "Sigma Oasis.", "sources": ["setlist.fm"]}):
        response = client.post("/query", json={"question": "What opened most in 2024?"})
    assert response.status_code == 200


def test_query_response_has_answer_and_sources(client):
    with patch("main.run_query", return_value={"answer": "Sigma Oasis.", "sources": ["setlist.fm"]}):
        response = client.post("/query", json={"question": "What opened most in 2024?"})
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert isinstance(body["sources"], list)


def test_query_passes_question_to_agent(client):
    with patch("main.run_query") as mock_agent:
        mock_agent.return_value = {"answer": "ok", "sources": []}
        client.post("/query", json={"question": "longest Tweezer?"})
    mock_agent.assert_called_once_with("longest Tweezer?")


def test_query_returns_500_on_agent_error(client):
    with patch("main.run_query", side_effect=Exception("API down")):
        response = client.post("/query", json={"question": "anything"})
    assert response.status_code == 500
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Implement main.py**

Write to `backend/main.py`:
```python
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_query

app = FastAPI(title="PhishBot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        result = run_query(request.question)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: Run all backend tests**

```bash
pytest tests/ -v
```

Expected: all 16 tests pass.

- [ ] **Step 5: Smoke-test the live server**

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
  -d '{"question": "What is the most common Phish show opener in 2024?"}' | python3 -m json.tool
```

Expected: JSON with `"answer"` and `"sources": ["setlist.fm"]`. May take 5–15 seconds (real API calls). Stop the server with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/main.py backend/tests/test_main.py
git commit -m "feat: add FastAPI /query endpoint with tests"
```

---

### Task 5: Frontend scaffolding

**Files:**
- Create: all files under `frontend/`

- [ ] **Step 1: Scaffold Vite + React + TypeScript project**

```bash
cd /Users/bskern/Projects/phishbot
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install Tailwind v3 and test dependencies**

```bash
npm install -D tailwindcss@3 postcss autoprefixer
npm install -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

- [ ] **Step 3: Initialize Tailwind**

```bash
npx tailwindcss init -p
```

This creates `tailwind.config.js` and `postcss.config.js`.

- [ ] **Step 4: Configure tailwind.config.js**

Write to `frontend/tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 5: Update vite.config.ts to add Vitest config**

Write to `frontend/vite.config.ts`:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts',
  },
})
```

- [ ] **Step 6: Create test setup file**

Write to `frontend/src/test-setup.ts`:
```ts
import '@testing-library/jest-dom'
```

- [ ] **Step 7: Replace src/index.css with Tailwind directives and shimmer keyframe**

Write to `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

- [ ] **Step 8: Add test script to package.json**

Open `frontend/package.json`. In the `"scripts"` section, add:
```json
"test": "vitest"
```

The scripts section should look like:
```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "preview": "vite preview",
  "test": "vitest"
}
```

- [ ] **Step 9: Delete boilerplate files you won't use**

```bash
rm frontend/src/App.css frontend/src/assets/react.svg
```

- [ ] **Step 10: Verify the dev server starts**

```bash
cd /Users/bskern/Projects/phishbot/frontend && npm run dev
```

Expected: server on http://localhost:5173. You'll see the default Vite/React page. Stop with Ctrl+C.

- [ ] **Step 11: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add frontend/
git commit -m "chore: scaffold frontend with Vite, React, TypeScript, Tailwind v3, Vitest"
```

---

### Task 6: QueryInput component

**Files:**
- Create: `frontend/src/components/QueryInput.tsx`
- Create: `frontend/src/components/QueryInput.test.tsx`

- [ ] **Step 1: Create the components directory**

```bash
mkdir -p /Users/bskern/Projects/phishbot/frontend/src/components
```

- [ ] **Step 2: Write the failing tests**

Write to `frontend/src/components/QueryInput.test.tsx`:
```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryInput } from './QueryInput'

test('renders the textarea', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByPlaceholderText(/ask anything about phish/i)).toBeInTheDocument()
})

test('renders the Ask button', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument()
})

test('renders the three example chips', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByText('longest Tweezer?')).toBeInTheDocument()
  expect(screen.getByText('Maze in first set 2024')).toBeInTheDocument()
  expect(screen.getByText('Carini stats')).toBeInTheDocument()
})

test('calls onSubmit with typed question when Ask clicked', async () => {
  const onSubmit = vi.fn()
  render(<QueryInput onSubmit={onSubmit} disabled={false} />)
  await userEvent.type(screen.getByRole('textbox'), 'longest Tweezer?')
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  expect(onSubmit).toHaveBeenCalledWith('longest Tweezer?')
})

test('clicking a chip populates the textarea', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  fireEvent.click(screen.getByText('Carini stats'))
  expect(screen.getByRole('textbox')).toHaveValue('Carini stats')
})

test('does not call onSubmit when question is empty', () => {
  const onSubmit = vi.fn()
  render(<QueryInput onSubmit={onSubmit} disabled={false} />)
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  expect(onSubmit).not.toHaveBeenCalled()
})

test('Ask button is disabled when disabled prop is true', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={true} />)
  expect(screen.getByRole('button', { name: /ask/i })).toBeDisabled()
})
```

- [ ] **Step 3: Run tests to see them fail**

```bash
cd /Users/bskern/Projects/phishbot/frontend
npx vitest run
```

Expected: `Cannot find module './QueryInput'`

- [ ] **Step 4: Implement QueryInput.tsx**

Write to `frontend/src/components/QueryInput.tsx`:
```tsx
import { useState, KeyboardEvent } from 'react'

const CHIPS = ['longest Tweezer?', 'Maze in first set 2024', 'Carini stats']

interface Props {
  onSubmit: (question: string) => void
  disabled: boolean
}

export function QueryInput({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit()
    }
  }

  return (
    <div className="rounded-xl border border-[#222] bg-[#111] p-4 flex flex-col gap-3 focus-within:border-[#00c9a0] transition-colors">
      <span className="text-[10px] font-semibold tracking-widest text-[#444] uppercase">Ask</span>
      <textarea
        className="bg-transparent outline-none text-[#e1e1e1] text-base resize-none placeholder-[#333]"
        rows={2}
        placeholder="Ask anything about Phish..."
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <div className="flex items-center justify-between gap-2">
        <div className="flex gap-1.5 flex-wrap">
          {CHIPS.map(chip => (
            <button
              key={chip}
              type="button"
              onClick={() => setValue(chip)}
              className="text-[11px] text-[#444] bg-[#161616] border border-[#1e1e1e] rounded-md px-2 py-1 hover:text-[#00c9a0] hover:border-[#00c9a040] transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled}
          className="bg-[#00c9a0] text-black font-semibold text-[13px] rounded-lg px-4 py-2 whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Ask →
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/bskern/Projects/phishbot/frontend
npx vitest run
```

Expected: all 7 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add frontend/src/components/QueryInput.tsx frontend/src/components/QueryInput.test.tsx
git commit -m "feat: add QueryInput component with tests"
```

---

### Task 7: ResultCard component

**Files:**
- Create: `frontend/src/components/ResultCard.tsx`
- Create: `frontend/src/components/ResultCard.test.tsx`

- [ ] **Step 1: Write the failing tests**

Write to `frontend/src/components/ResultCard.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { ResultCard } from './ResultCard'

test('renders answer text when not loading', () => {
  render(
    <ResultCard
      question="What opened most in 2024?"
      answer="Sigma Oasis opened 7 shows."
      sources={['setlist.fm']}
      loading={false}
    />
  )
  expect(screen.getByText('Sigma Oasis opened 7 shows.')).toBeInTheDocument()
})

test('echoes the question in the header', () => {
  render(
    <ResultCard
      question="What opened most in 2024?"
      answer="Sigma Oasis opened 7 shows."
      sources={['setlist.fm']}
      loading={false}
    />
  )
  expect(screen.getByText('"What opened most in 2024?"')).toBeInTheDocument()
})

test('renders source tags', () => {
  render(
    <ResultCard
      question="test"
      answer="answer"
      sources={['setlist.fm', 'phish.net']}
      loading={false}
    />
  )
  expect(screen.getByText('setlist.fm')).toBeInTheDocument()
  expect(screen.getByText('phish.net')).toBeInTheDocument()
})

test('shows Thinking label when loading', () => {
  render(
    <ResultCard question="test" answer="" sources={[]} loading={true} />
  )
  expect(screen.getByText('Thinking...')).toBeInTheDocument()
})

test('hides ANSWER label when loading', () => {
  render(
    <ResultCard question="test" answer="" sources={[]} loading={true} />
  )
  expect(screen.queryByText('ANSWER')).not.toBeInTheDocument()
})

test('shows ANSWER label when not loading', () => {
  render(
    <ResultCard question="test" answer="some answer" sources={[]} loading={false} />
  )
  expect(screen.getByText('ANSWER')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd /Users/bskern/Projects/phishbot/frontend
npx vitest run
```

Expected: `Cannot find module './ResultCard'`

- [ ] **Step 3: Implement ResultCard.tsx**

Write to `frontend/src/components/ResultCard.tsx`:
```tsx
interface Props {
  question: string
  answer: string
  sources: string[]
  loading: boolean
}

export function ResultCard({ question, answer, sources, loading }: Props) {
  return (
    <div className="rounded-xl border border-[#1e1e1e] bg-[#111] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1a1a1a]">
        {loading ? (
          <span className="text-[10px] font-semibold tracking-widest text-[#444] uppercase">
            Thinking...
          </span>
        ) : (
          <>
            <span className="text-[10px] font-semibold tracking-widest text-[#444] uppercase">
              ANSWER
            </span>
            <span className="text-[12px] text-[#555] italic truncate max-w-xs">
              "{question}"
            </span>
          </>
        )}
      </div>

      <div className="px-4 py-5 min-h-16">
        {loading ? (
          <div
            className="h-0.5 rounded-full"
            style={{
              background: 'linear-gradient(90deg, #111 0%, #00c9a0 50%, #111 100%)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 1.5s infinite',
            }}
          />
        ) : (
          <p className="text-[15px] text-[#ccc] leading-relaxed">{answer}</p>
        )}
      </div>

      {!loading && sources.length > 0 && (
        <div className="flex items-center gap-2 px-4 py-2.5 border-t border-[#1a1a1a]">
          <span className="text-[10px] text-[#333]">sources</span>
          {sources.map(src => (
            <span
              key={src}
              className="text-[10px] text-[#444] bg-[#161616] border border-[#1e1e1e] rounded px-1.5 py-0.5"
            >
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run all frontend tests**

```bash
cd /Users/bskern/Projects/phishbot/frontend
npx vitest run
```

Expected: all 13 tests pass (7 QueryInput + 6 ResultCard).

- [ ] **Step 5: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add frontend/src/components/ResultCard.tsx frontend/src/components/ResultCard.test.tsx
git commit -m "feat: add ResultCard component with tests"
```

---

### Task 8: App.tsx and end-to-end wiring

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/index.html`

- [ ] **Step 1: Write App.tsx**

Write to `frontend/src/App.tsx`:
```tsx
import { useState } from 'react'
import { QueryInput } from './components/QueryInput'
import { ResultCard } from './components/ResultCard'

type AppState = 'idle' | 'loading' | 'result' | 'error'

interface Result {
  question: string
  answer: string
  sources: string[]
}

export default function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState('')

  async function handleSubmit(question: string) {
    setAppState('loading')
    setCurrentQuestion(question)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        const body = await response.json()
        throw new Error(body.detail ?? 'Request failed')
      }

      const data = await response.json()
      setResult({ question, answer: data.answer, sources: data.sources })
      setAppState('result')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setAppState('error')
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e1e1e1] flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl flex flex-col gap-6">

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-[#00c9a0] rounded-[50%_50%_50%_50%/60%_60%_40%_40%] flex items-center justify-center text-lg">
              🐟
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-[22px] font-bold tracking-tight">
                Phish<span className="text-[#00c9a0]">Bot</span>
              </span>
              <span className="text-[10px] font-semibold text-[#555] tracking-widest uppercase">AI</span>
            </div>
          </div>
          <div className="flex gap-1.5">
            {['setlist.fm', 'phish.net', 'web'].map(src => (
              <span
                key={src}
                className="text-[10px] text-[#444] bg-[#161616] border border-[#222] rounded-full px-2 py-0.5"
              >
                {src}
              </span>
            ))}
          </div>
        </div>

        <QueryInput onSubmit={handleSubmit} disabled={appState === 'loading'} />

        {appState === 'loading' && (
          <ResultCard question={currentQuestion} answer="" sources={[]} loading={true} />
        )}

        {appState === 'result' && result && (
          <ResultCard
            question={result.question}
            answer={result.answer}
            sources={result.sources}
            loading={false}
          />
        )}

        {appState === 'error' && (
          <div className="rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-[13px] text-red-400">
            {error}
          </div>
        )}

      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update main.tsx**

Write to `frontend/src/main.tsx`:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

- [ ] **Step 3: Update index.html**

Edit `frontend/index.html`. Replace the `<head>` content with:
```html
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/vite.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <title>PhishBot</title>
</head>
```

- [ ] **Step 4: End-to-end test**

Terminal 1 — start the backend:
```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
uvicorn main:app --reload
```

Terminal 2 — start the frontend:
```bash
cd /Users/bskern/Projects/phishbot/frontend
npm run dev
```

Open http://localhost:5173 in a browser.

Try these queries:
1. Type "What is the most common Phish opener in 2024?" → click Ask →. Expected: loading shimmer, then an answer from Claude citing setlist.fm.
2. Click the "longest Tweezer?" chip → click Ask →. Expected: Claude notes that setlist.fm doesn't have duration data, and explains this limitation.
3. Type something invalid like "abc" → Expected: answer card appears with whatever Claude returns.

- [ ] **Step 5: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add frontend/src/App.tsx frontend/src/main.tsx frontend/index.html
git commit -m "feat: wire App.tsx state machine and complete end-to-end query flow"
```

---

## Done

At this point you have a working PhishBot:
- All 16 backend tests pass
- All 13 frontend tests pass
- Real queries flow from the UI → FastAPI → Claude → setlist.fm → back to UI

**Next step (Phase 2):** Add LangGraph to orchestrate the tool-use loop, then wire in phish.net, ihoz.com, and web search as additional tools.
