from unittest.mock import patch, MagicMock

SAMPLE_SETLIST = {
    "eventDate": "01-08-2024",
    "venue": {
        "name": "Merriweather Post Pavilion",
        "city": {"name": "Columbia"},
    },
    "sets": {
        "set": [
            {
                "encore": 0,
                "song": [
                    {"name": "Sigma Oasis"},
                    {"name": "Tweezer"},
                    {"name": "Chalk Dust Torture"},
                ],
            },
            {
                "encore": 1,
                "song": [{"name": "Tweezer Reprise"}],
            },
        ]
    },
}


def _mock_response(setlists: list) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"total": len(setlists), "setlist": setlists}
    mock.raise_for_status = MagicMock()
    return mock


def test_tool_definition_shape():
    from tools.setlistfm import TOOL_DEFINITION

    assert TOOL_DEFINITION["name"] == "search_setlists"
    assert "description" in TOOL_DEFINITION
    assert "input_schema" in TOOL_DEFINITION
    props = TOOL_DEFINITION["input_schema"]["properties"]
    assert "year" in props
    assert "song" in props
    assert "position" in props


def test_search_returns_source():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists()
    assert result["source"] == "setlist.fm"


def test_search_returns_date_and_venue():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists()
    assert result["results"][0]["date"] == "01-08-2024"
    assert "Merriweather" in result["results"][0]["venue"]


def test_search_by_song_filters_to_matching_songs():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(song="Tweezer")
    matched = [s["name"] for s in result["results"][0]["songs"]]
    assert "Tweezer" in matched
    assert "Sigma Oasis" not in matched


def test_search_opener_returns_first_non_encore_song():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(position="opener")
    songs = result["results"][0]["songs"]
    assert len(songs) == 1
    assert songs[0]["name"] == "Sigma Oasis"


def test_search_closer_returns_last_non_encore_song():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(position="closer")
    songs = result["results"][0]["songs"]
    assert len(songs) == 1
    assert songs[0]["name"] == "Chalk Dust Torture"


def test_search_passes_year_param_to_api():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([])) as mock_get:
        search_setlists(year="2024")
    assert mock_get.call_args[1]["params"]["year"] == "2024"


def test_empty_results():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([])):
        result = search_setlists(song="Nonexistent Song XYZ")
    assert result["results"] == []
    assert result["total"] == 0


def test_search_by_song_and_position_filters_correctly():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(song="Sigma Oasis", position="opener")
    # Sigma Oasis is the opener, so it should be found
    assert len(result["results"]) == 1
    assert result["results"][0]["songs"][0]["name"] == "Sigma Oasis"

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(song="Tweezer", position="opener")
    # Tweezer is NOT the opener (Sigma Oasis is), so this setlist should be skipped entirely
    assert result["results"] == []


def test_search_includes_encore_songs_in_any_position():
    from tools.setlistfm import search_setlists

    with patch("tools.setlistfm.httpx.get", return_value=_mock_response([SAMPLE_SETLIST])):
        result = search_setlists(song="Tweezer")
    song_names = [s["name"] for s in result["results"][0]["songs"]]
    # Both Tweezer and Tweezer Reprise (encore) match the substring filter
    assert "Tweezer" in song_names
    assert "Tweezer Reprise" in song_names
    # The encore flag distinguishes them
    encore_flags = {s["name"]: s["encore"] for s in result["results"][0]["songs"]}
    assert encore_flags["Tweezer"] == False
    assert encore_flags["Tweezer Reprise"] == True
