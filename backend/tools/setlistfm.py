import os
from typing import Optional, Literal
import httpx
from langchain_core.tools import tool

SETLISTFM_BASE = "https://api.setlist.fm/rest/1.0"


@tool
def search_setlists(
    year: Optional[str] = None,
    song: Optional[str] = None,
    date: Optional[str] = None,
    position: Literal["opener", "closer", "any"] = "any",
) -> dict:
    """Search Phish setlists by year, song name, or specific date.

    Use 'date' (YYYY-MM-DD) to get the full setlist for a specific show — all songs, all sets.
    Use 'song' to find all shows where a song was played.
    Use 'position' ('opener', 'closer', or 'any') to filter by set position.
    Use 'year' to narrow results to a specific year.
    """
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

        if date and not song:
            result["sets"] = sets_data

        results.append(result)

    return {"total": data.get("total", 0), "results": results, "source": "setlist.fm"}
