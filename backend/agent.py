import json
import anthropic
from tools.setlistfm import TOOL_DEFINITION as SETLISTFM_TOOL, search_setlists
from tools.phishnet import (
    JAMCHARTS_TOOL, SONG_HISTORY_TOOL, SEARCH_SHOWS_TOOL,
    get_jamcharts, get_song_history, search_shows,
)
from tools.discography import SEARCH_DISCOGRAPHY_TOOL, search_discography
from tools.ihoz import GET_SONG_STATS_TOOL, get_song_stats

client = anthropic.Anthropic()

TOOL_DISPATCH = {
    "search_setlists": search_setlists,
    "get_jamcharts": get_jamcharts,
    "get_song_history": get_song_history,
    "search_shows": search_shows,
    "search_discography": search_discography,
    "get_song_stats": get_song_stats,
}

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 3}

TOOLS = [
    SETLISTFM_TOOL, JAMCHARTS_TOOL, SONG_HISTORY_TOOL,
    SEARCH_SHOWS_TOOL, SEARCH_DISCOGRAPHY_TOOL, GET_SONG_STATS_TOOL,
    WEB_SEARCH_TOOL,
]

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


def run_query(question: str, history: list[dict] | None = None) -> dict:
    messages = list(history or []) + [{"role": "user", "content": question}]
    sources = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Track web search usage (handled server-side; appears as server_tool_use blocks)
        for block in response.content:
            if getattr(block, "type", None) == "server_tool_use" and getattr(block, "name", None) == "web_search":
                sources.append("web")

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
