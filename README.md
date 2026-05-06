# PhishBot

A conversational AI assistant for Phish concert history. Ask questions in plain English — PhishBot pulls from multiple data sources and answers with specific dates, venues, durations, and counts.

## What it can answer

- *"When was Tweezer last played and what followed it?"*
- *"What are the best versions of Carini?"*
- *"How many shows has Phish played in Minnesota?"*
- *"Is Antelope typically a Set 1 or Set 2 song?"*
- *"What album is Sigma Oasis on?"*
- *"Any upcoming tour dates?"*

## Data sources

| Source | What it provides |
|---|---|
| [phish.net](https://phish.net) | Jam charts, song history, shows by state |
| [setlist.fm](https://www.setlist.fm) | Full setlists, shows by venue |
| [ihoz.com](http://www.ihoz.com) | Gap tracking, set distribution, before/after transitions |
| Anthropic web search | Tour news, ticket info, recent announcements |

> **Note:** The phish.net API is restricted to non-commercial use. See their [terms of service](https://api.phish.net).

## Stack

- **Backend:** Python 3.11+, FastAPI, Anthropic SDK (Claude Sonnet, native tool use)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS

## Setup

### API keys

You'll need three API keys:

- **Anthropic** — [console.anthropic.com](https://console.anthropic.com)
- **phish.net** — [api.phish.net](https://api.phish.net)
- **setlist.fm** — [api.setlist.fm](https://api.setlist.fm)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in your API keys

uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Running tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest tests/ -v

# Frontend
cd frontend && npm test -- --run
```

## License

MIT — see [LICENSE](LICENSE).
