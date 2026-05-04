# PhishBot Design Spec
_2026-05-04_

## Overview

A natural language interface over Phish's data ecosystem. Ask a question in plain English, get an answer drawn from structured setlist data. Built as a learning project for the coordinator/subagent agentic pattern using the Anthropic SDK and LangGraph (introduced in a later phase).

Local use only — no auth, no multi-user concerns.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + Vite + Tailwind | Fast DX, easy to make dark mode look polished |
| Backend | FastAPI (Python) | Lightweight, async, great for AI backends |
| LLM | Anthropic Claude (`claude-sonnet-4-6`) | Tool use API, direct SDK |
| Agent framework | Anthropic SDK tool use (Phase 1), LangGraph (Phase 2) | Learn the pattern before introducing the framework |
| Primary data | setlist.fm API | Reliable, well-maintained, API key in hand |
| Future data | phish.net API (if viable), ihoz.com scraper, web search | Add as tools later |

---

## Project Structure

```
phishbot/
├── backend/
│   ├── main.py              # FastAPI app, CORS, /query endpoint
│   ├── agent.py             # Claude + tool use orchestration
│   ├── tools/
│   │   ├── __init__.py
│   │   └── setlistfm.py     # Tool definition + setlist.fm API implementation
│   ├── requirements.txt
│   └── .env                 # ANTHROPIC_API_KEY, SETLISTFM_API_KEY
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── components/
│   │       ├── QueryInput.tsx   # Input box + example chips + submit button
│   │       └── ResultCard.tsx   # Answer display + source attribution + loading state
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
└── .gitignore
```

---

## API Contract

### `POST /query`

**Request:**
```json
{ "question": "What's the most common opener in 2024?" }
```

**Response:**
```json
{
  "answer": "The most common opener in 2024 was Sigma Oasis, which opened 7 shows...",
  "sources": ["setlist.fm"]
}
```

**Error (HTTP 500):**
```json
{ "error": "Something went wrong", "detail": "..." }
```

Success returns HTTP 200. CORS is open to `http://localhost:5173` (Vite dev server default).

---

## Backend Design

### Agent flow (`agent.py`)

```
question
  ↓
Claude (claude-sonnet-4-6) + tool definitions
  ↓
Claude returns tool_use block → { name: "search_setlists", input: { year, song, position } }
  ↓
setlistfm.py implementation → raw API results
  ↓
Tool result appended to message history
  ↓
Claude synthesizes final answer
  ↓
{ answer: str, sources: list[str] }
```

The tool definition (JSON schema) and implementation (HTTP call) live together in `setlistfm.py`. This separation is intentional: it's what makes the LangGraph migration in Phase 2 feel natural — LangGraph takes over managing the tool use loop, not the tools themselves.

### Initial tool: `search_setlists`

```python
{
  "name": "search_setlists",
  "description": "Search Phish setlists by year, song, or both. Returns matching shows with set positions.",
  "input_schema": {
    "type": "object",
    "properties": {
      "year": { "type": "string", "description": "4-digit year, e.g. '2024'" },
      "song": { "type": "string", "description": "Song name to search for" },
      "position": { "type": "string", "enum": ["opener", "closer", "any"], "description": "Set position filter" }
    },
    "required": []
  }
}
```

All fields optional — Claude decides what to pass based on the question.

---

## Frontend Design

### Visual style

- Dark mode: `#0a0a0a` background, `#111` card surfaces, `#222` borders
- Accent: `#00c9a0` (teal) for highlights, the Ask button, and key data points in answers
- Font: Inter
- Branding: "PhishBot" wordmark with teal "Bot", fish emoji logo mark, "AI" badge

### Components

**`QueryInput`**
- Textarea (auto-resizes) + "Ask →" button
- Row of example query chips below the input: "longest Tweezer?", "Maze in first set 2024", "Carini stats"
- Chips populate the input on click
- Submit on button click or Cmd/Ctrl+Enter

**`ResultCard`**
- Header row: "ANSWER" label + echoed question (truncated)
- Body: answer text, teal highlights on key data points
- Footer: source tags (e.g., "setlist.fm")
- Loading state: animated shimmer bar in place of content
- Hidden until first query submitted

### State machine (App.tsx)

```
idle → loading (on submit) → result (on response) → idle (on new query)
                           → error (on failure)
```

---

## Learning Progression

This project is designed to be built in phases that match the learning sequence from the build ideas doc:

**Phase 1 (this spec):**
1. Scaffold project structure (frontend + backend)
2. Wire setlist.fm API as a basic Python module
3. Add Claude tool use via Anthropic SDK
4. Connect FastAPI → agent → frontend
5. Get one end-to-end query working

**Phase 2 (separate spec, later):**
- Introduce LangGraph to orchestrate the tool use loop
- Add phish.net API tool (if viable)
- Add ihoz.com scraper tool
- Add web search tool
- Coordinator → subagent pattern in full

---

## Environment

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
SETLISTFM_API_KEY=...
```

setlist.fm API key is in hand. phish.net API key status uncertain — treat as a future addition, not a dependency.

---

## Out of Scope (Phase 1)

- Authentication / user accounts
- Conversation history persistence
- Streaming responses
- Deployment (local only)
- LangGraph orchestration
- Multiple data sources beyond setlist.fm
