# Conversational Mode Design

## Goal

Make PhishBot conversational so follow-up questions can reference prior answers in the same session, without changing the single-answer UI or adding server-side session state.

## Architecture

The frontend owns the conversation history as an in-memory list of messages. Each request sends the full prior history to the backend alongside the new question. The backend prepends that history to Claude's message array before running the tool loop. The backend remains stateless — no sessions, no storage.

## API Contract

**Request** — `POST /query`
```json
{
  "question": "what about carini?",
  "history": [
    { "role": "user",      "content": "when was tweezer last played?" },
    { "role": "assistant", "content": "Tweezer was last played on December 31, 2025..." }
  ]
}
```
`history` is optional and defaults to `[]`. The response shape is unchanged: `{ "answer": str, "sources": [str] }`.

## Backend Changes

**`backend/agent.py`**
- `run_query(question: str, history: list[dict] = []) -> dict`
- Build `messages` by prepending `history` then appending the new user question:
  ```python
  messages = history + [{"role": "user", "content": question}]
  ```
- No other logic changes.

**`backend/main.py`**
- `QueryRequest` adds `history: list[dict] = []`
- Pass `history` through to `run_query`

## Frontend Changes

**`frontend/src/App.tsx`**

New type:
```typescript
interface ConversationMessage {
  role: "user" | "assistant"
  content: string
  sources: string[]
}
```

State changes:
- Remove `history: Result[]` and `addToHistory` / `restoreFromHistory`
- Add `messages: ConversationMessage[]` (starts empty)
- `currentQuestion` and `result` remain for loading/error display

On submit:
1. Build `history` payload from `messages` (strip `sources`, keep `role` + `content`)
2. POST `{ question, history }` to backend
3. On success: append user message and assistant message to `messages`, update `result`

"New Conversation" button:
- Visible only when `messages.length > 0`
- Clears `messages` to `[]` and `result` to `null`, sets `appState` to `'idle'`
- Placed in the header row next to the source chips

Remove the recent questions history strip entirely.

**`frontend/src/components/QueryInput.tsx`** — no changes.  
**`frontend/src/components/ResultCard.tsx`** — no changes.

## Testing

**`backend/tests/test_agent.py`**
- `test_run_query_passes_history_to_claude` — verify that when `history` is provided, the messages sent to Claude include those prior turns before the new question
- `test_run_query_empty_history_still_works` — verify default `history=[]` produces correct single-message call

**`backend/tests/test_main.py`**
- `test_query_endpoint_accepts_history_field` — POST with a `history` list, verify 200 and answer returned

**`frontend/src/App.test.tsx`** (create if it doesn't exist)
- `test_messages_accumulate_across_questions` — after two successful submits, `messages` has 4 entries (2 user, 2 assistant)
- `test_new_conversation_clears_messages` — after messages exist, clicking "New Conversation" resets to empty

## Out of Scope

- Persisting conversation to localStorage (natural next step, not included here)
- Maximum conversation length / token budgeting (not needed at this scale)
- Multi-conversation history (one active conversation at a time)
