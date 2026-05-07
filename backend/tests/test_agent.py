import json
import pytest
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def test_run_query_returns_dict_with_answer_and_sources():
    from agent import run_query

    state = {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Sigma Oasis opened 7 shows."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("What was the most common opener in 2024?")

    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)


def test_run_query_answer_text_matches_final_ai_message():
    from agent import run_query

    state = {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Sigma Oasis opened 7 shows."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("What was the most common opener in 2024?")

    assert result["answer"] == "Sigma Oasis opened 7 shows."


def test_run_query_extracts_source_from_tool_message():
    from agent import run_query

    tool_result = {"total": 1, "results": [], "source": "setlist.fm"}
    ai_with_call = AIMessage(
        content="",
        tool_calls=[{"name": "search_setlists", "args": {}, "id": "call_1", "type": "tool_call"}],
    )
    state = {
        "messages": [
            HumanMessage(content="test"),
            ai_with_call,
            ToolMessage(content=json.dumps(tool_result), name="search_setlists", tool_call_id="call_1"),
            AIMessage(content="Sigma Oasis opened 7 shows in 2024."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("What was the most common opener in 2024?")

    assert "Sigma Oasis" in result["answer"]
    assert "setlist.fm" in result["sources"]


def test_run_query_deduplicates_sources():
    from agent import run_query

    tool_result = {"total": 0, "results": [], "source": "setlist.fm"}
    ai_with_call = AIMessage(
        content="",
        tool_calls=[{"name": "search_setlists", "args": {}, "id": "call_1", "type": "tool_call"}],
    )
    state = {
        "messages": [
            HumanMessage(content="test"),
            ai_with_call,
            ToolMessage(content=json.dumps(tool_result), name="search_setlists", tool_call_id="call_1"),
            AIMessage(content="No results."),
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("anything")

    assert result["sources"].count("setlist.fm") == 1


def test_run_query_prepends_history_as_langchain_messages():
    from agent import run_query

    history = [
        {"role": "user", "content": "when was tweezer last played?"},
        {"role": "assistant", "content": "Tweezer was last played on December 31, 2025."},
    ]
    state = {"messages": [AIMessage(content="Carini was played recently.")]}
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        run_query("what about carini?", history=history)

    call_messages = mock_app.invoke.call_args[0][0]["messages"]
    assert isinstance(call_messages[0], HumanMessage)
    assert call_messages[0].content == "when was tweezer last played?"
    assert isinstance(call_messages[1], AIMessage)
    assert call_messages[1].content == "Tweezer was last played on December 31, 2025."
    assert isinstance(call_messages[2], HumanMessage)
    assert call_messages[2].content == "what about carini?"


def test_run_query_empty_history_sends_single_user_message():
    from agent import run_query

    state = {"messages": [AIMessage(content="Some answer.")]}
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        run_query("what opened the show?")

    call_messages = mock_app.invoke.call_args[0][0]["messages"]
    assert len(call_messages) == 1
    assert isinstance(call_messages[0], HumanMessage)
    assert call_messages[0].content == "what opened the show?"


def test_graph_has_agent_and_tools_nodes():
    import agent
    assert "agent" in agent._app.nodes
    assert "tools" in agent._app.nodes


def test_local_tools_list_contains_all_six_tools():
    import agent
    tool_names = [t.name for t in agent.LOCAL_TOOLS]
    assert "search_setlists" in tool_names
    assert "get_jamcharts" in tool_names
    assert "get_song_history" in tool_names
    assert "search_shows" in tool_names
    assert "search_discography" in tool_names
    assert "get_song_stats" in tool_names


def test_web_search_tool_config_is_correct_type():
    import agent
    assert agent.WEB_SEARCH_TOOL["type"] == "web_search_20250305"
    assert agent.WEB_SEARCH_TOOL["name"] == "web_search"


def test_run_query_detects_web_search_source_from_tool_calls():
    from agent import run_query

    ai_with_web = AIMessage(
        content="",
        tool_calls=[{"name": "web_search", "args": {}, "id": "call_web", "type": "tool_call"}],
    )
    final_ai = AIMessage(content="Phish announced a 2026 summer tour.")
    state = {
        "messages": [
            HumanMessage(content="Any tour news?"),
            ai_with_web,
            final_ai,
        ]
    }
    with patch("agent._app") as mock_app:
        mock_app.invoke.return_value = state
        result = run_query("Any Phish tour news?")

    assert "web" in result["sources"]
