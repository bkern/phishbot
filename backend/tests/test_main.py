import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_query_returns_200(client):
    with patch("main.run_query", return_value={"answer": "Sigma Oasis.", "sources": ["setlist.fm"]}):
        response = client.post("/query", json={"question": "What opened most in 2024?"})
    assert response.status_code == 200


def test_query_response_has_answer_and_sources(client):
    with patch("main.run_query", return_value={"answer": "Sigma Oasis.", "sources": ["setlist.fm"]}):
        response = client.post("/query", json={"question": "What opened most in 2024?"})
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert isinstance(body["sources"], list)


def test_query_passes_question_to_agent(client):
    with patch("main.run_query") as mock_agent:
        mock_agent.return_value = {"answer": "ok", "sources": []}
        client.post("/query", json={"question": "longest Tweezer?"})
    mock_agent.assert_called_once_with("longest Tweezer?")


def test_query_returns_500_on_agent_error(client):
    with patch("main.run_query", side_effect=Exception("API down")):
        response = client.post("/query", json={"question": "anything"})
    assert response.status_code == 500
