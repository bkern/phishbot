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


def test_agent_dispatch_includes_search_shows():
    import agent
    assert "search_shows" in agent.TOOL_DISPATCH


def test_agent_dispatch_includes_search_discography():
    import agent
    assert "search_discography" in agent.TOOL_DISPATCH


def test_agent_dispatch_includes_get_song_stats():
    import agent
    assert "get_song_stats" in agent.TOOL_DISPATCH


def test_agent_tools_list_includes_web_search():
    import agent
    tool_types = [t.get("type", "") for t in agent.TOOLS]
    assert any("web_search" in t for t in tool_types)


def test_run_query_attributes_web_source_from_server_tool_use():
    from agent import run_query

    web_block = MagicMock()
    web_block.type = "server_tool_use"
    web_block.name = "web_search"

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Phish announced a 2026 summer tour."

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [web_block, text_block]

    with patch("agent.client") as mock_client:
        mock_client.messages.create.return_value = response
        result = run_query("Any Phish tour news?")

    assert "web" in result["sources"]


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
