import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START
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
