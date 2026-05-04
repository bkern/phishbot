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
