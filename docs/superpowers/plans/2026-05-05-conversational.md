# Conversational Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PhishBot conversational so follow-up questions can reference prior answers, without changing the single-answer UI or adding server-side session state.

**Architecture:** The frontend accumulates conversation history as a list of `{role, content}` pairs and sends the full history with each request. The backend prepends that history to Claude's messages array before running the tool loop. The backend stays stateless.

**Tech Stack:** Python/FastAPI (backend), React/TypeScript/Vitest (frontend), @testing-library/react

---

## File Map

**Modify:**
- `backend/agent.py` — add `history` parameter to `run_query`
- `backend/main.py` — add `history` field to `QueryRequest`, pass to `run_query`
- `backend/tests/test_agent.py` — add history tests
- `backend/tests/test_main.py` — add history tests, fix broken existing test
- `frontend/src/App.tsx` — replace history strip with conversation state + New Conversation button

**Create:**
- `frontend/src/App.test.tsx` — App-level conversation tests

---

### Task 1: agent.py — history parameter

**Files:**
- Modify: `backend/agent.py`
- Modify: `backend/tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_agent.py` (keep all existing tests intact):

```python
def test_run_query_prepends_history_to_messages():
    from agent import run_query

    history = [
        {"role": "user", "content": "when was tweezer last played?"},
        {"role": "assistant", "content": "Tweezer was last played on December 31, 2025."},
    ]

    with patch("agent.client") as mock_client:
        mock_client.messages.create.return_value = _text_response("Carini was last played recently.")
        run_query("what about carini?", history=history)

    call_messages = mock_client.messages.create.call_args[1]["messages"]
    assert call_messages[0] == {"role": "user", "content": "when was tweezer last played?"}
    assert call_messages[1] == {"role": "assistant", "content": "Tweezer was last played on December 31, 2025."}
    assert call_messages[2] == {"role": "user", "content": "what about carini?"}


def test_run_query_empty_history_sends_single_user_message():
    from agent import run_query

    with patch("agent.client") as mock_client:
        mock_client.messages.create.return_value = _text_response("Some answer.")
        run_query("what opened the show?")

    call_messages = mock_client.messages.create.call_args[1]["messages"]
    assert len(call_messages) == 1
    assert call_messages[0] == {"role": "user", "content": "what opened the show?"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_agent.py::test_run_query_prepends_history_to_messages tests/test_agent.py::test_run_query_empty_history_sends_single_user_message -v
```

Expected: FAIL — `run_query() got an unexpected keyword argument 'history'`

- [ ] **Step 3: Update agent.py**

Change only the `run_query` function signature and `messages` construction. Read the current file first; everything else stays the same. Replace the function definition and first line of the loop setup:

```python
def run_query(question: str, history: list[dict] | None = None) -> dict:
    messages = list(history or []) + [{"role": "user", "content": question}]
    sources = []
```

The rest of `run_query` is unchanged.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent.py::test_run_query_prepends_history_to_messages tests/test_agent.py::test_run_query_empty_history_sends_single_user_message -v
```

Expected: both PASS

- [ ] **Step 5: Run full backend test suite**

```bash
pytest tests/ -q
```

Expected: all 72 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/agent.py backend/tests/test_agent.py
git commit -m "feat: run_query accepts optional conversation history"
```

---

### Task 2: main.py — history in API request

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/tests/test_main.py`

- [ ] **Step 1: Write failing tests and fix the broken existing test**

The existing `test_query_passes_question_to_agent` currently asserts `mock_agent.assert_called_once_with("longest Tweezer?")`. After the change, `run_query` will be called with `history=[]` too, so that assertion will break. Fix it and add new tests.

Replace the existing `test_query_passes_question_to_agent` and append new tests in `backend/tests/test_main.py`:

```python
def test_query_passes_question_to_agent(client):
    with patch("main.run_query") as mock_agent:
        mock_agent.return_value = {"answer": "ok", "sources": []}
        client.post("/query", json={"question": "longest Tweezer?"})
    mock_agent.assert_called_once_with("longest Tweezer?", history=[])


def test_query_accepts_history_field(client):
    history = [
        {"role": "user", "content": "when was tweezer last played?"},
        {"role": "assistant", "content": "Tweezer was last played on December 31, 2025."},
    ]
    with patch("main.run_query", return_value={"answer": "Carini info.", "sources": []}):
        response = client.post("/query", json={"question": "what about carini?", "history": history})
    assert response.status_code == 200


def test_query_passes_history_to_agent(client):
    history = [
        {"role": "user", "content": "when was tweezer last played?"},
        {"role": "assistant", "content": "Tweezer was last played on December 31, 2025."},
    ]
    with patch("main.run_query") as mock_agent:
        mock_agent.return_value = {"answer": "ok", "sources": []}
        client.post("/query", json={"question": "what about carini?", "history": history})
    mock_agent.assert_called_once_with("what about carini?", history=history)
```

- [ ] **Step 2: Run tests to verify the new ones fail**

```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
pytest tests/test_main.py -v
```

Expected: `test_query_passes_question_to_agent` FAIL (assertion mismatch), `test_query_accepts_history_field` FAIL, `test_query_passes_history_to_agent` FAIL.

- [ ] **Step 3: Update main.py**

Replace the full content of `backend/main.py`:

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
    history: list[dict] = []


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        result = run_query(request.question, history=request.history)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_main.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 5: Run full backend test suite**

```bash
pytest tests/ -q
```

Expected: all 74 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add backend/main.py backend/tests/test_main.py
git commit -m "feat: /query endpoint accepts optional conversation history"
```

---

### Task 3: App.tsx — conversational frontend

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

function mockFetch(answer: string, sources: string[] = []) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ answer, sources }),
  } as unknown as Response)
}

afterEach(() => {
  vi.restoreAllMocks()
})

test('sends empty history on first question', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))

  await waitFor(() => {
    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    const body = JSON.parse(call[1].body)
    expect(body.history).toEqual([])
  })
})

test('sends accumulated history on second question', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  await waitFor(() => screen.getByText('ANSWER'))

  mockFetch('Carini was last played recently.')
  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'what about carini?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))

  await waitFor(() => {
    const secondCall = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[1]
    const body = JSON.parse(secondCall[1].body)
    expect(body.history).toHaveLength(2)
    expect(body.history[0]).toEqual({
      role: 'user',
      content: 'when was tweezer last played?',
    })
    expect(body.history[1]).toEqual({
      role: 'assistant',
      content: 'Tweezer was last played December 31, 2025.',
    })
  })
})

test('new conversation button appears after first answer', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  expect(screen.queryByText('New Conversation')).not.toBeInTheDocument()

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))

  await waitFor(() => screen.getByText('New Conversation'))
})

test('new conversation button resets state', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  await waitFor(() => screen.getByText('New Conversation'))

  fireEvent.click(screen.getByText('New Conversation'))

  expect(screen.queryByText('New Conversation')).not.toBeInTheDocument()
  expect(screen.queryByText('ANSWER')).not.toBeInTheDocument()
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bskern/Projects/phishbot/frontend
npm test -- App.test.tsx --run
```

Expected: FAIL — `App.test.tsx` can't find `New Conversation` button, history assertions fail.

- [ ] **Step 3: Replace App.tsx**

Write the full content of `frontend/src/App.tsx`:

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

interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  sources: string[]
}

export default function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [messages, setMessages] = useState<ConversationMessage[]>([])

  function handleNewConversation() {
    setMessages([])
    setResult(null)
    setAppState('idle')
    setError(null)
    setCurrentQuestion('')
  }

  async function handleSubmit(question: string) {
    setAppState('loading')
    setCurrentQuestion(question)
    setError(null)

    const history = messages.map(({ role, content }) => ({ role, content }))

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
      })

      if (!response.ok) {
        const body = await response.json()
        throw new Error(body.detail ?? 'Request failed')
      }

      const data = await response.json()
      const newResult = { question, answer: data.answer, sources: data.sources }
      setResult(newResult)
      setMessages(prev => [
        ...prev,
        { role: 'user', content: question, sources: [] },
        { role: 'assistant', content: data.answer, sources: data.sources },
      ])
      setAppState('result')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setAppState('error')
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e1e1e1] flex flex-col items-center px-6 py-10">
      <div className="w-full max-w-3xl lg:max-w-5xl xl:max-w-6xl flex flex-col gap-6">

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-[#00c9a0] rounded-[50%_50%_50%_50%/60%_60%_40%_40%] flex items-center justify-center text-xl">
              🐟
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight">
                Phish<span className="text-[#00c9a0]">Bot</span>
              </span>
              <span className="text-xs font-semibold text-[#555] tracking-widest uppercase">AI</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                type="button"
                onClick={handleNewConversation}
                className="text-xs text-[#555] hover:text-[#888] transition-colors px-3 py-1 rounded border border-[#222] hover:border-[#333]"
              >
                New Conversation
              </button>
            )}
            {['setlist.fm', 'phish.net', 'web'].map(src => (
              <span
                key={src}
                className="text-xs text-[#777] bg-[#161616] border border-[#2a2a2a] rounded-full px-3 py-1"
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
          <div className="rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run frontend tests to verify they pass**

```bash
cd /Users/bskern/Projects/phishbot/frontend
npm test -- App.test.tsx --run
```

Expected: all 4 App tests pass.

- [ ] **Step 5: Run full frontend test suite**

```bash
npm test -- --run
```

Expected: all tests pass (existing QueryInput + ResultCard tests plus 4 new App tests).

- [ ] **Step 6: Smoke test in the browser**

Terminal 1 — start backend:
```bash
cd /Users/bskern/Projects/phishbot/backend
source .venv/bin/activate
uvicorn main:app --reload
```

Terminal 2 — start frontend:
```bash
cd /Users/bskern/Projects/phishbot/frontend
npm run dev
```

Open `http://localhost:5173`. Ask "when was Tweezer last played?" then ask "what usually comes after it?" — the second question should reference the first without needing to restate the song. Verify the "New Conversation" button appears after the first answer and clears the state when clicked. Stop both servers.

- [ ] **Step 7: Commit**

```bash
cd /Users/bskern/Projects/phishbot
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: conversational mode with history and New Conversation button"
```

---

## Done

PhishBot now maintains conversation context within a session. Follow-up questions like "what about Carini?" or "when was that?" work because the full message history is sent with each request. The "New Conversation" button resets everything cleanly. The backend remains stateless.
