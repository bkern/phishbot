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


def test_agent_dispatch_includes_phishnet_tools():
    import agent
    assert "get_jamcharts" in agent.TOOL_DISPATCH
    assert "get_song_history" in agent.TOOL_DISPATCH
    assert "search_setlists" in agent.TOOL_DISPATCH
