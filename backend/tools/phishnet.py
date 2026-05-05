import os
import re
from urllib.parse import quote as url_quote
import httpx

PHISHNET_BASE = "https://api.phish.net/v5"

JAMCHARTS_TOOL = {
    "name": "get_jamcharts",
    "description": (
        "Get community jam charts for a Phish song — the notable, highly-rated performances "
        "with track durations. Use this for questions about the best or longest versions of a song, "
        "or when asked about must-hear jams. Returns each jam's date, venue, set, duration, and notes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Song name, e.g. 'Tweezer', 'Bathtub Gin', 'Carini'",
            },
        },
        "required": ["song"],
    },
}

SONG_HISTORY_TOOL = {
    "name": "get_song_history",
    "description": (
        "Get the history, background, and metadata for a Phish song from phish.net's "
        "editorial database. Use this for questions about a song's origins, meaning, or story."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Song name, e.g. 'You Enjoy Myself', 'Wilson', 'Harry Hood'",
            },
        },
        "required": ["song"],
    },
}


def _song_to_slug(song: str) -> str:
    # Take only the first song if a segue notation like "Tweezer > Lifeboy" is passed
    song = song.split(">")[0]
    slug = song.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def get_jamcharts(song: str) -> dict:
    slug = _song_to_slug(song)
    response = httpx.get(
        f"{PHISHNET_BASE}/jamcharts/slug/{slug}.json",
        params={"apikey": os.environ["PHISHNET_API_KEY"]},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    jams = []
    for entry in data.get("data", []):
        jam = {
            "date": entry.get("showdate", ""),
            "venue": f"{entry.get('venue', '')}, {entry.get('city', '')}, {entry.get('state', '')}",
            "set": entry.get("set", ""),
            "duration": entry.get("tracktime", ""),
        }
        notes = entry.get("jamnotesshort", "").strip()
        if notes:
            jam["notes"] = notes
        jams.append(jam)

    return {"song": song, "total": data.get("total", len(jams)), "jams": jams, "source": "phish.net"}


def get_song_history(song: str) -> dict:
    slug = _song_to_slug(song)
    response = httpx.get(
        f"{PHISHNET_BASE}/songdata/slug/{slug}.json",
        params={"apikey": os.environ["PHISHNET_API_KEY"]},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    entries = data.get("data", [])
    if not entries:
        return {"song": None, "history": None, "source": "phish.net"}

    entry = entries[0]
    return {
        "song": entry.get("song"),
        "history": entry.get("history") or None,
        "lyrics": entry.get("lyrics") or None,
        "source": "phish.net",
    }


SEARCH_SHOWS_TOOL = {
    "name": "search_shows",
    "description": (
        "Search Phish shows by US state or venue name. "
        "Use for questions like 'how many shows in Minnesota', "
        "'what venues has Phish played in Colorado', or "
        "'all shows at Madison Square Garden'. "
        "Provide state (2-letter abbreviation) OR venue name — not both. "
        "Optionally filter by year."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "2-letter US state abbreviation, e.g. 'MN' for Minnesota, 'CO' for Colorado, 'NY' for New York",
            },
            "venue": {
                "type": "string",
                "description": "Venue name, e.g. 'Madison Square Garden', 'Sphere', 'Red Rocks Amphitheatre'",
            },
            "year": {
                "type": "string",
                "description": "4-digit year to filter results, e.g. '2024'",
            },
        },
        "required": [],
    },
}


def search_shows(
    state: str = None,
    venue: str = None,
    year: str = None,
) -> dict:
    apikey = os.environ["PHISHNET_API_KEY"]

    if venue:
        venue_response = httpx.get(
            f"{PHISHNET_BASE}/venues/venuename/{url_quote(venue)}.json",
            params={"apikey": apikey},
            timeout=10.0,
        )
        venue_response.raise_for_status()
        venues = venue_response.json().get("data", [])
        if not venues:
            return {"shows": [], "total": 0, "source": "phish.net"}
        venueid = venues[0]["venueid"]

        shows_response = httpx.get(
            f"{PHISHNET_BASE}/shows/venueid/{venueid}.json",
            params={"apikey": apikey},
            timeout=10.0,
        )
        shows_response.raise_for_status()
        all_shows = shows_response.json().get("data", [])

    elif state:
        shows_response = httpx.get(
            f"{PHISHNET_BASE}/shows/state/{state}.json",
            params={"apikey": apikey},
            timeout=10.0,
        )
        shows_response.raise_for_status()
        all_shows = shows_response.json().get("data", [])

    else:
        return {"shows": [], "total": 0, "source": "phish.net"}

    if year:
        all_shows = [s for s in all_shows if s.get("showdate", "").startswith(year)]

    shows = [
        {
            "date": s.get("showdate", ""),
            "venue": s.get("venue", ""),
            "city": s.get("city", ""),
            "state": s.get("state", ""),
        }
        for s in all_shows
    ]

    return {"shows": shows, "total": len(shows), "source": "phish.net"}
