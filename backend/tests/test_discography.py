def test_tool_definition_shape():
    from tools.discography import SEARCH_DISCOGRAPHY_TOOL

    assert SEARCH_DISCOGRAPHY_TOOL["name"] == "search_discography"
    assert "description" in SEARCH_DISCOGRAPHY_TOOL
    props = SEARCH_DISCOGRAPHY_TOOL["input_schema"]["properties"]
    assert "song" in props
    assert "album" in props


def test_song_lookup_finds_correct_album():
    from tools.discography import search_discography

    result = search_discography(song="Kill Devil Falls")
    assert len(result["matches"]) == 1
    assert result["matches"][0]["album"] == "Joy"
    assert result["matches"][0]["year"] == 2009


def test_song_lookup_is_case_insensitive():
    from tools.discography import search_discography

    result = search_discography(song="kill devil falls")
    assert len(result["matches"]) == 1
    assert result["matches"][0]["album"] == "Joy"


def test_song_lookup_partial_match():
    from tools.discography import search_discography

    result = search_discography(song="Number Line")
    assert any("Backwards Down the Number Line" in m["song"] for m in result["matches"])


def test_song_lookup_not_found_returns_empty():
    from tools.discography import search_discography

    result = search_discography(song="Nonexistent Song XYZ")
    assert result["matches"] == []
    assert result["source"] == "discography"


def test_album_lookup_returns_year_and_tracklist():
    from tools.discography import search_discography

    result = search_discography(album="Rift")
    assert len(result["albums"]) == 1
    album = result["albums"][0]
    assert album["year"] == 1993
    assert "Maze" in album["songs"]
    assert "Horn" in album["songs"]


def test_album_lookup_is_case_insensitive():
    from tools.discography import search_discography

    result = search_discography(album="farmhouse")
    assert len(result["albums"]) == 1
    assert result["albums"][0]["title"] == "Farmhouse"


def test_album_lookup_partial_match():
    from tools.discography import search_discography

    result = search_discography(album="Picture of Nectar")
    assert len(result["albums"]) == 1
    assert result["albums"][0]["year"] == 1992


def test_album_lookup_not_found_returns_empty():
    from tools.discography import search_discography

    result = search_discography(album="Nonexistent Album XYZ")
    assert result["albums"] == []
    assert result["source"] == "discography"


def test_no_params_returns_all_albums():
    from tools.discography import search_discography

    result = search_discography()
    assert len(result["albums"]) >= 10
    titles = [a["title"] for a in result["albums"]]
    assert "Junta" in titles
    assert "Joy" in titles
    assert "Sigma Oasis" in titles


def test_returns_source():
    from tools.discography import search_discography

    assert search_discography(song="Maze")["source"] == "discography"
    assert search_discography(album="Rift")["source"] == "discography"
    assert search_discography()["source"] == "discography"
