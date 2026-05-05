import os
import httpx

SETLISTFM_BASE = "https://api.setlist.fm/rest/1.0"

TOOL_DEFINITION = {
    "name": "search_setlists",
    "description": (
        "Search Phish setlists by year, song name, or specific date. "
        "Use 'date' (YYYY-MM-DD) to get the full setlist for a specific show — all songs, all sets. "
        "Use 'song' to find all shows where a song was played. "
        "Use 'position' to find show openers or closers."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Specific show date in YYYY-MM-DD format, e.g. '2026-04-18'. Returns the complete setlist for that show.",
            },
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
    date: str = None,
    position: str = "any",
) -> dict:
    params = {"artistName": "Phish", "p": 1}
    if year:
        params["year"] = year
    if song:
        params["songName"] = song
    if date:
        # setlist.fm expects DD-MM-YYYY; we accept YYYY-MM-DD from Claude
        try:
            y, m, d = date.split("-")
            params["date"] = f"{d}-{m}-{y}"
        except ValueError:
            pass

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
        show_date = setlist.get("eventDate", "")
        venue_obj = setlist.get("venue", {})
        venue = f"{venue_obj.get('name', '')}, {venue_obj.get('city', {}).get('name', '')}"

        # Build flat song list and per-set structure simultaneously
        non_encore_idx = 0
        sets_data = []
        main_songs = []
        all_songs = []

        for set_data in setlist.get("sets", {}).get("set", []):
            is_encore = bool(set_data.get("encore", 0))
            if is_encore:
                set_label = "Encore"
            else:
                non_encore_idx += 1
                set_label = f"Set {non_encore_idx}"

            set_song_names = []
            for song_obj in set_data.get("song", []):
                name = song_obj.get("name", "")
                entry = {"name": name, "encore": is_encore, "set": set_label}
                all_songs.append(entry)
                set_song_names.append(name)
                if not is_encore:
                    main_songs.append(entry)

            if set_song_names:
                sets_data.append({"label": set_label, "songs": set_song_names})

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

        result = {"date": show_date, "venue": venue, "songs": candidates}

        # Full setlist mode: include structured sets when fetching by date with no song filter
        if date and not song:
            result["sets"] = sets_data

        results.append(result)

    return {"total": data.get("total", 0), "results": results, "source": "setlist.fm"}
