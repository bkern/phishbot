# LangGraph Port — Design Spec

**Date:** 2026-05-07  
**Branch:** `feat/langgraph`  
**Motivation:** Learning — understand LangGraph by porting a real project to it.

---

## Overview

Port `backend/agent.py` from a hand-rolled `while True` ReAct loop (Anthropic SDK) to an explicit LangGraph `StateGraph` using `langchain-anthropic` (`ChatAnthropic`). The FastAPI interface and all tool logic are unchanged; only the agent orchestration layer changes.

---

## Graph Architecture

Two nodes connected by a conditional edge:

```
START
  │
  ▼
[agent]  — calls ChatAnthropic with all tools bound
  │
  ├─ tool_calls present? ──► [tools]  — ToolNode dispatches to the right function
  │                               │
  │                               └──────────────────────► [agent]
  │
  └─ no tool calls ──► END
```

- `StateGraph(MessagesState)` — built-in LangGraph state class; holds `messages: list[BaseMessage]`, appended automatically on each node visit.
- `tools_condition` — LangGraph built-in conditional edge; checks last message for tool calls.
- Graph is compiled once at module load, invoked per request via `graph.invoke()`.

---

## Tool Layer

### Local tools (`@tool` decorator)

Each tool function in `backend/tools/` gets a `@tool` decorator from `langchain_core.tools`. Existing function signatures and logic are unchanged. The decorator registers name, description, and schema — replacing the raw `TOOL_DEFINITION` dicts. `ToolNode` handles dispatch automatically by tool name, replacing the `TOOL_DISPATCH` dict.

Affected files:
- `tools/phishnet.py` — `get_jamcharts`, `get_song_history`, `search_shows`
- `tools/setlistfm.py` — `search_setlists`
- `tools/discography.py` — `search_discography`
- `tools/ihoz.py` — `get_song_stats`

### Web search (special case)

Anthropic's server-side web search (`"type": "web_search_20250305"`) has no local function to dispatch — Anthropic handles it. It is passed as a raw dict alongside the `@tool`-decorated tools when binding to `ChatAnthropic`. `ToolNode` ignores it (no local handler); Anthropic resolves it server-side as before.

---

## State & History

Incoming `history` (list of `{"role": ..., "content": ...}` dicts from the frontend) is converted to LangChain `HumanMessage`/`AIMessage` objects before `graph.invoke()`. The current question is appended as a `HumanMessage`. `MessagesState` accumulates all messages across the graph run.

Source tracking: after `graph.invoke()` returns, iterate the final message list to find `ToolMessage` entries and extract their `name` (tool name → data source). Web search sources are detected from `AIMessage` tool call metadata.

---

## FastAPI Interface

No changes to `main.py`. Same `/query` endpoint, `QueryRequest`/`QueryResponse` models, and CORS config. `run_query(question, history)` in `agent.py` is the only function that changes internals — its signature and return type (`{"answer": str, "sources": list[str]}`) remain identical.

---

## Dependencies

Add to `backend/requirements.txt`:
- `langgraph`
- `langchain-anthropic`
- `langchain-core`

Existing packages unchanged.

---

## Tests

- `tests/test_agent.py` — rewrite to test `graph.invoke()` instead of the manual loop. Mock `ChatAnthropic` responses.
- `tests/test_phishnet.py`, `test_setlistfm.py`, `test_ihoz.py`, `test_discography.py` — no changes; tool functions are unaffected.
- `tests/test_main.py` — no changes; FastAPI interface is unchanged.

---

## Out of Scope

- Checkpointing / persistence (no database)
- Streaming tokens to the frontend
- `create_react_agent` prebuilt (hidden internals, not useful for learning)
- Multi-node per-source routing (overcomplicated for this use case)
- Frontend changes
