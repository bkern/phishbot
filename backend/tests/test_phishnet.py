from unittest.mock import patch, MagicMock


def _mock_response(data: list, total: int = None) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {
        "error": False,
        "total": total if total is not None else len(data),
        "data": data,
    }
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JAMCHART_DATA = [
    {
        "showid": "1234567890",
        "showdate": "1994-07-08",
        "venue": "Great Woods Center",
        "city": "Mansfield",
        "state": "MA",
        "set": "2",
        "tracktime": "38:23",
        "recommended": 1,
        "jamnotesshort": "Epic segue into Lifeboy",
    },
    {
        "showid": "0987654321",
        "showdate": "1997-11-22",
        "venue": "Hampton Coliseum",
        "city": "Hampton",
        "state": "VA",
        "set": "2",
        "tracktime": "31:07",
        "recommended": 1,
        "jamnotesshort": "",
    },
]

SAMPLE_SONGDATA = [
    {
        "songid": "432",
        "song": "Tweezer",
        "slug": "tweezer",
        "nickname": "",
        "history": "Debuted on January 20, 1990 at University of Vermont. "
                   "A vehicle for extended improvisation.",
        "lyrics": "Step into the freezer...",
    }
]


def test_jamcharts_tool_definition_shape():
    from tools.phishnet import JAMCHARTS_TOOL

    assert JAMCHARTS_TOOL["name"] == "get_jamcharts"
    assert "description" in JAMCHARTS_TOOL
    assert "input_schema" in JAMCHARTS_TOOL
    props = JAMCHARTS_TOOL["input_schema"]["properties"]
    assert "song" in props
    assert JAMCHARTS_TOOL["input_schema"]["required"] == ["song"]


def test_song_history_tool_definition_shape():
    from tools.phishnet import SONG_HISTORY_TOOL

    assert SONG_HISTORY_TOOL["name"] == "get_song_history"
    assert "description" in SONG_HISTORY_TOOL
    props = SONG_HISTORY_TOOL["input_schema"]["properties"]
    assert "song" in props
    assert SONG_HISTORY_TOOL["input_schema"]["required"] == ["song"]


def test_song_to_slug_simple():
    from tools.phishnet import _song_to_slug

    assert _song_to_slug("Tweezer") == "tweezer"


def test_song_to_slug_multi_word():
    from tools.phishnet import _song_to_slug

    assert _song_to_slug("Bathtub Gin") == "bathtub-gin"
    assert _song_to_slug("You Enjoy Myself") == "you-enjoy-myself"
    assert _song_to_slug("Chalk Dust Torture") == "chalk-dust-torture"


def test_get_jamcharts_returns_source():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert result["source"] == "phish.net"


def test_get_jamcharts_returns_jams_with_date_venue_duration():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    jam = result["jams"][0]
    assert jam["date"] == "1994-07-08"
    assert "Great Woods" in jam["venue"]
    assert jam["duration"] == "38:23"


def test_get_jamcharts_includes_notes_when_present():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert result["jams"][0]["notes"] == "Epic segue into Lifeboy"


def test_get_jamcharts_omits_notes_when_empty():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert "notes" not in result["jams"][1]


def test_get_jamcharts_passes_slug_to_api():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])) as mock_get:
        get_jamcharts(song="Bathtub Gin")
    url = mock_get.call_args[0][0]
    assert "bathtub-gin" in url


def test_get_song_history_returns_source():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SONGDATA)):
        result = get_song_history(song="Tweezer")
    assert result["source"] == "phish.net"


def test_get_song_history_returns_name_and_history():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SONGDATA)):
        result = get_song_history(song="Tweezer")
    assert result["song"] == "Tweezer"
    assert "1990" in result["history"]


def test_get_song_history_returns_not_found_when_empty():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = get_song_history(song="Nonexistent XYZ")
    assert result["song"] is None
    assert result["history"] is None


def test_get_jamcharts_includes_set_field():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA)):
        result = get_jamcharts(song="Tweezer")
    assert result["jams"][0]["set"] == "2"


def test_get_jamcharts_includes_total():
    from tools.phishnet import get_jamcharts

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_JAMCHART_DATA, total=47)):
        result = get_jamcharts(song="Tweezer")
    assert result["total"] == 47


def test_song_to_slug_strips_segue_notation():
    from tools.phishnet import _song_to_slug

    assert _song_to_slug("Tweezer > Lifeboy") == "tweezer"


def test_get_song_history_not_found_includes_source():
    from tools.phishnet import get_song_history

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = get_song_history(song="Nonexistent XYZ")
    assert result["source"] == "phish.net"


# ── search_shows tests ────────────────────────────────────────────────────────

SAMPLE_SHOWS = [
    {
        "showdate": "2023-07-15",
        "venue": "Target Center",
        "city": "Minneapolis",
        "state": "MN",
        "country": "USA",
    },
    {
        "showdate": "2019-08-02",
        "venue": "Xcel Energy Center",
        "city": "Saint Paul",
        "state": "MN",
        "country": "USA",
    },
]

SAMPLE_VENUE = [
    {
        "venueid": "123",
        "venuename": "Madison Square Garden",
        "city": "New York",
        "state": "NY",
        "country": "USA",
    }
]


def test_search_shows_tool_definition_shape():
    from tools.phishnet import SEARCH_SHOWS_TOOL

    assert SEARCH_SHOWS_TOOL["name"] == "search_shows"
    assert "description" in SEARCH_SHOWS_TOOL
    assert "input_schema" in SEARCH_SHOWS_TOOL
    props = SEARCH_SHOWS_TOOL["input_schema"]["properties"]
    assert "state" in props
    assert "venue" in props
    assert "year" in props


def test_search_shows_by_state_returns_source():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN")
    assert result["source"] == "phish.net"


def test_search_shows_by_state_returns_shows_with_correct_fields():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN")
    show = result["shows"][0]
    assert show["date"] == "2023-07-15"
    assert show["venue"] == "Target Center"
    assert show["city"] == "Minneapolis"
    assert show["state"] == "MN"


def test_search_shows_by_state_passes_state_to_url():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])) as mock_get:
        search_shows(state="CO")
    url = mock_get.call_args[0][0]
    assert "CO" in url


def test_search_shows_returns_total_count():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN")
    assert result["total"] == 2


def test_search_shows_by_state_filters_by_year():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response(SAMPLE_SHOWS)):
        result = search_shows(state="MN", year="2023")
    assert result["total"] == 1
    assert result["shows"][0]["date"] == "2023-07-15"


def test_search_shows_by_venue_makes_two_api_calls():
    from tools.phishnet import search_shows

    venue_resp = _mock_response(SAMPLE_VENUE)
    shows_resp = _mock_response(SAMPLE_SHOWS[:1])

    with patch("tools.phishnet.httpx.get", side_effect=[venue_resp, shows_resp]) as mock_get:
        result = search_shows(venue="Madison Square Garden")

    assert mock_get.call_count == 2
    assert result["source"] == "phish.net"
    assert result["shows"][0]["date"] == "2023-07-15"


def test_search_shows_by_venue_uses_venueid_in_second_call():
    from tools.phishnet import search_shows

    venue_resp = _mock_response([{
        "venueid": "789",
        "venuename": "Sphere",
        "city": "Las Vegas",
        "state": "NV",
        "country": "USA",
    }])
    shows_resp = _mock_response([])

    with patch("tools.phishnet.httpx.get", side_effect=[venue_resp, shows_resp]) as mock_get:
        search_shows(venue="Sphere")

    second_url = mock_get.call_args_list[1][0][0]
    assert "789" in second_url


def test_search_shows_venue_not_found_returns_empty():
    from tools.phishnet import search_shows

    with patch("tools.phishnet.httpx.get", return_value=_mock_response([])):
        result = search_shows(venue="Nonexistent Venue XYZ")

    assert result["shows"] == []
    assert result["total"] == 0
    assert result["source"] == "phish.net"
