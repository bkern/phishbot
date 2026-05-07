from unittest.mock import patch, MagicMock

FIXTURE_HTML = """
<html><body>
<h1>Tweezer</h1>
<strong>Times played</strong>
<table border=1>
<tr><th>Date</th><th>Gap</th><th>Set</th><th>Pos.</th><th>Before</th><th>After</th></tr>
<tr><td>3/28/90</td><td>214</td><td>1</td><td>5/12</td>
  <td><a href="/cgi/phish?song=Walk+Away">Walk Away</a></td>
  <td><a href="/cgi/phish?song=Uncle+Pen">Uncle Pen</a></td></tr>
<tr><td>4/5/90</td><td>3</td><td>2</td><td>6/13</td>
  <td><a href="/cgi/phish?song=Donna+Lee">Donna Lee</a></td>
  <td><a href="/cgi/phish?song=Fee">Fee</a></td></tr>
<tr><td>4/7/90</td><td>2</td><td>1</td><td>10/13</td>
  <td><a href="/cgi/phish?song=Possum">Possum</a></td>
  <td><a href="/cgi/phish?song=Mike%27s+Song">Mike's Song</a></td></tr>
<tr><td>6/2/90</td><td>5</td><td>E</td><td>1/2</td>
  <td>***</td>
  <td><a href="/cgi/phish?song=Divided+Sky">Divided Sky</a></td></tr>
<tr><td>12/31/25</td><td>6</td><td>3</td><td>4/6</td>
  <td><a href="/cgi/phish?song=Auld+Lang+Syne">Auld Lang Syne</a></td>
  <td><a href="/cgi/phish?song=Piper">Piper</a></td></tr>
</table>
</body></html>
"""


def _mock_get(html: str = FIXTURE_HTML) -> MagicMock:
    mock = MagicMock()
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_get_song_stats_tool_name():
    from tools.ihoz import get_song_stats
    assert get_song_stats.name == "get_song_stats"


def test_get_song_stats_tool_has_song_arg():
    from tools.ihoz import get_song_stats
    schema = get_song_stats.args_schema.model_json_schema()
    assert "song" in schema["properties"]
    assert "song" in schema.get("required", [])


def test_returns_times_played():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert result["times_played"] == 5


def test_returns_last_played():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert result["last_played"] == "12/31/25"


def test_returns_source():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert result["source"] == "ihoz.com"


def test_set_breakdown_counts_correctly():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    breakdown = result["set_breakdown"]
    assert breakdown["Set 1"] == 2
    assert breakdown["Set 2"] == 1
    assert breakdown["Encore"] == 1
    assert breakdown["Set 3"] == 1


def test_set_breakdown_normalizes_encore():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert "Encore" in result["set_breakdown"]
    assert "E" not in result["set_breakdown"]


def test_top_after_counts_correctly():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    after_songs = [e["song"] for e in result["top_after"]]
    assert "Uncle Pen" in after_songs
    assert "Fee" in after_songs


def test_before_skips_unknown_marker():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    before_songs = [e["song"] for e in result["top_before"]]
    assert "***" not in before_songs


def test_recent_plays_returns_last_ten_or_fewer():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert len(result["recent_plays"]) <= 10
    assert result["recent_plays"][-1]["date"] == "12/31/25"


def test_recent_plays_entry_shape():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()):
        result = get_song_stats.invoke({"song": "Tweezer"})
    play = result["recent_plays"][0]
    assert "date" in play
    assert "gap" in play
    assert "set" in play
    assert "before" in play
    assert "after" in play


def test_url_encodes_multi_word_song():
    from tools.ihoz import get_song_stats
    with patch("tools.ihoz.httpx.get", return_value=_mock_get()) as mock_get:
        get_song_stats.invoke({"song": "Bathtub Gin"})
    url = mock_get.call_args[0][0]
    assert "Bathtub+Gin" in url or "Bathtub%20Gin" in url


def test_http_error_returns_error_dict():
    from tools.ihoz import get_song_stats
    import httpx
    with patch("tools.ihoz.httpx.get", side_effect=httpx.HTTPError("connection failed")):
        result = get_song_stats.invoke({"song": "Tweezer"})
    assert "error" in result
    assert result["source"] == "ihoz.com"
