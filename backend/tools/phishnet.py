import os
import re
from typing import Optional
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


def _shows_from_setlistfm(venue: str) -> list[dict]:
    """Venue-by-name search via setlist.fm (phish.net venue endpoint is access-restricted)."""
    response = httpx.get(
        "https://api.setlist.fm/rest/1.0/search/setlists",
        headers={
            "x-api-key": os.environ["SETLISTFM_API_KEY"],
            "Accept": "application/json",
        },
        params={"artistName": "Phish", "venueName": venue, "p": 1},
        timeout=10.0,
    )
    response.raise_for_status()
    shows = []
    for s in response.json().get("setlist", []):
        # setlist.fm returns dates as DD-MM-YYYY — convert to YYYY-MM-DD
        raw_date = s.get("eventDate", "")
        try:
            d, m, y = raw_date.split("-")
            showdate = f"{y}-{m}-{d}"
        except ValueError:
            showdate = raw_date
        venue_obj = s.get("venue", {})
        city_obj = venue_obj.get("city", {})
        shows.append({
            "showdate": showdate,
            "venue": venue_obj.get("name", ""),
            "city": city_obj.get("name", ""),
            "state": city_obj.get("stateCode", ""),
        })
    return shows


def search_shows(
    state: Optional[str] = None,
    venue: Optional[str] = None,
    year: Optional[str] = None,
) -> dict:
    try:
        if venue:
            # phish.net venue-by-name endpoint is access-restricted; use setlist.fm instead
            all_shows = _shows_from_setlistfm(venue)

        elif state:
            response = httpx.get(
                f"{PHISHNET_BASE}/shows/state/{state}.json",
                params={"apikey": os.environ["PHISHNET_API_KEY"]},
                timeout=10.0,
            )
            response.raise_for_status()
            raw = response.json().get("data", [])
            # phish.net returns shows for all artists — filter to Phish only
            all_shows = [
                {
                    "showdate": s.get("showdate", ""),
                    "venue": s.get("venue", ""),
                    "city": s.get("city", ""),
                    "state": s.get("state", ""),
                }
                for s in raw
                if s.get("artist_name", "").lower() == "phish"
            ]

        else:
            return {"shows": [], "total": 0, "source": "phish.net"}

    except httpx.HTTPStatusError as e:
        return {"shows": [], "total": 0, "source": "phish.net",
                "error": f"API error: {e.response.status_code}"}

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
