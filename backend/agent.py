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
    "Be specific: cite dates, venues, durations, and counts when you have them. "
    "Write in plain prose only — no markdown, no bullet points, no bold, no headers, no tables, no emojis. "
    "Use simple sentences and commas to separate lists."
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
