import os
import httpx

SETLISTFM_BASE = "https://api.setlist.fm/rest/1.0"

TOOL_DEFINITION = {
    "name": "search_setlists",
    "description": (
        "Search Phish setlists by year, song name, or both. "
        "Returns matching shows with song details and set positions. "
        "Use 'position' to find show openers or closers."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "year": {
                "type": "string",
                "description": "4-digit year, e.g. '2024'",
            },
            "song": {
                "type": "string",
                "description": "Song name to search for, e.g. 'Tweezer', 'Maze'",
            },
            "position": {
                "type": "string",
                "enum": ["opener", "closer", "any"],
                "description": (
                    "'opener' = first song of the show (excluding encores), "
                    "'closer' = last song before encores, "
                    "'any' = no position filter."
                ),
            },
        },
        "required": [],
    },
}


def search_setlists(
    year: str = None,
    song: str = None,
    position: str = "any",
) -> dict:
    params = {"artistName": "Phish", "p": 1}
    if year:
        params["year"] = year
    if song:
        params["songName"] = song

    response = httpx.get(
        f"{SETLISTFM_BASE}/search/setlists",
        headers={
            "x-api-key": os.environ["SETLISTFM_API_KEY"],
            "Accept": "application/json",
        },
        params=params,
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for setlist in data.get("setlist", [])[:20]:
        date = setlist.get("eventDate", "")
        venue_obj = setlist.get("venue", {})
        venue = f"{venue_obj.get('name', '')}, {venue_obj.get('city', {}).get('name', '')}"

        main_songs = []
        all_songs = []
        for set_data in setlist.get("sets", {}).get("set", []):
            is_encore = bool(set_data.get("encore", 0))
            for song_obj in set_data.get("song", []):
                entry = {"name": song_obj.get("name", ""), "encore": is_encore}
                all_songs.append(entry)
                if not is_encore:
                    main_songs.append(entry)

        opener = main_songs[:1]
        closer = main_songs[-1:] if main_songs else []

        if position == "opener":
            candidates = opener
        elif position == "closer":
            candidates = closer
        else:
            candidates = all_songs

        if song:
            candidates = [s for s in candidates if song.lower() in s["name"].lower()]
            if not candidates:
                continue

        results.append({"date": date, "venue": venue, "songs": candidates})

    return {"total": data.get("total", 0), "results": results, "source": "setlist.fm"}
