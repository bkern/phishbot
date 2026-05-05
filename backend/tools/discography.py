from typing import Optional

DISCOGRAPHY = [
    {
        "title": "The White Tape",
        "year": 1984,
        "label": "Self-released (officially released 1999 via Phish.com)",
        "notes": "Early rehearsal cassette, circulated as a bootleg for years before official release.",
        "songs": [
            "Camel Walk", "Fuck Your Face", "Halley's Comet", "Slave to the Traffic Light",
            "Standin' on the Corner", "Scissor Man", "Sneaking Sally Through the Alley",
            "Dog Log", "Letter to Jimmy Page", "Skippy the Wondermouse",
            "Flat Fee", "Swing Low Sweet Chariot",
        ],
    },
    {
        "title": "Junta",
        "year": 1989,
        "label": "Absolute A-Go-Go Records (reissued 1992)",
        "notes": "Self-released debut. Remastered and reissued commercially in 1992.",
        "songs": [
            "Fee", "You Enjoy Myself", "Fluffhead", "The Sloth", "Golgi Apparatus",
            "Foam", "Dinner and a Movie", "Divided Sky", "David Bowie", "Bike",
            "Union Federal", "Sanity", "Icculus",
        ],
    },
    {
        "title": "A Picture of Nectar",
        "year": 1992,
        "label": "Elektra",
        "songs": [
            "Llama", "Eliza", "Cavern", "Poor Heart", "Stash", "Manteca",
            "Guelah Papyrus", "Magilla", "The Landlady", "Glide", "Tweezer",
            "The Mango Song", "Chalk Dust Torture", "Faht", "Catapult", "Tweezer Reprise",
        ],
    },
    {
        "title": "Rift",
        "year": 1993,
        "label": "Elektra",
        "notes": "Concept album structured around a dream sequence.",
        "songs": [
            "Rift", "Fast Enough for You", "Lengthwise", "Maze", "Sparkle", "Horn",
            "The Wedge", "My Friend My Friend", "Weigh", "All Things Reconsidered",
            "Mound", "It's Ice", "The Horse", "Silent in the Morning",
        ],
    },
    {
        "title": "Hoist",
        "year": 1994,
        "label": "Elektra",
        "songs": [
            "Julius", "Down with Disease", "Why Don't We Do It in the Road?",
            "Riker's Mailbox", "Axilla (Part II)", "Lifeboy", "Sample in a Jar",
            "Demand", "If I Could", "Reba", "Wolfman's Brother", "Scent of a Mule",
            "Dog Faced Boy", "Keyboard Cavalry",
        ],
    },
    {
        "title": "Billy Breathes",
        "year": 1996,
        "label": "Elektra",
        "songs": [
            "Free", "Character Zero", "Waste", "Taste", "Cars Trucks Buses", "Talk",
            "Theme from the Bottom", "Train Song", "Bliss", "Billy Breathes",
            "Swept Away", "Steep", "Prince Caspian",
        ],
    },
    {
        "title": "The Story of the Ghost",
        "year": 1998,
        "label": "Elektra",
        "songs": [
            "Ghost", "Birds of a Feather", "Meat", "Guyute", "Fikus", "Shafty",
            "Limb by Limb", "Frankie Says", "Water in the Sky", "Roggae", "Mozambique",
            "The Inlaw Josie Wales", "Vultures", "Sleep", "Stay (Faraway, So Close!)",
        ],
    },
    {
        "title": "Farmhouse",
        "year": 2000,
        "label": "Elektra",
        "songs": [
            "Farmhouse", "Twist", "Bug", "Back on the Train", "Heavy Things",
            "Dirt", "Piper", "Sleep Again", "Sand", "First Tube",
        ],
    },
    {
        "title": "Round Room",
        "year": 2002,
        "label": "Elektra",
        "notes": "Recorded live-to-tape in the studio over five days.",
        "songs": [
            "Pebbles and Marbles", "Anything But Me", "Round Room", "Walls of the Cave",
            "Seven Below", "Waves", "Friday", "Mock Song", "Thunderhead",
            "All of These Dreams", "Plasma", "46 Days",
        ],
    },
    {
        "title": "Undermind",
        "year": 2004,
        "label": "Elektra / Rhino",
        "songs": [
            "Nothing", "Secret Smile", "Crowd Control", "Army of One", "Magnet",
            "Scabbard", "Air Safari", "A Song I Heard the Ocean Sing",
            "Two Versions of Me", "The Connection", "Access Me", "Inside Out",
        ],
    },
    {
        "title": "Joy",
        "year": 2009,
        "label": "JEMP Records",
        "notes": "First album after the 2004-2009 hiatus.",
        "songs": [
            "Backwards Down the Number Line", "Stealing Time from the Faulty Plan",
            "Sugar Shack", "Light", "Kill Devil Falls", "I Been Around", "Ocelot",
            "Time Turns Elastic", "Twenty Years Later", "Joy", "Alaska",
        ],
    },
    {
        "title": "Fuego",
        "year": 2014,
        "label": "JEMP Records",
        "songs": [
            "Fuego", "The Line", "Halfway to the Moon", "Devotion to a Dream",
            "Waiting All Night", "Wombat", "Winterqueen", "Sing Monica", "555", "Wingsuit",
        ],
    },
    {
        "title": "Big Boat",
        "year": 2016,
        "label": "JEMP Records",
        "songs": [
            "Friends", "Breath and Burning", "Things People Do", "Blaze On",
            "Tide Turns", "Miss You", "Petrichor", "Running Man", "More",
            "I Always Wanted It This Way", "Havana Affair", "Home",
        ],
    },
    {
        "title": "Kasvot Växt: i rokk",
        "year": 2018,
        "label": "JEMP Records",
        "notes": (
            "Released as Phish's Halloween 2018 musical costume, presented as recordings "
            "from an obscure Scandinavian prog-rock band 'Kasvot Växt'. "
            "The songs are original Phish compositions. Many also appear on Sigma Oasis."
        ),
        "songs": [
            "Mercury", "Lonely Trip", "Leaves", "Thread", "Drift While Sleeping",
            "Mull", "When Circus Comes", "Everything's Right", "Evolve",
            "Abstract", "Passing Through",
        ],
    },
    {
        "title": "Sigma Oasis",
        "year": 2020,
        "label": "JEMP Records",
        "notes": "Released during the COVID-19 pandemic. Studio versions of songs previewed at Halloween 2018.",
        "songs": [
            "Everything's Right", "No Men in No Man's Land", "Mercury", "Thread",
            "Leaves", "Sigma Oasis", "Steam", "Lonely Trip", "Evolve",
            "Light Much Brighter", "Turtle in the Clouds",
        ],
    },
]

SEARCH_DISCOGRAPHY_TOOL = {
    "name": "search_discography",
    "description": (
        "Look up Phish studio albums and song origins. "
        "Use 'song' to find which album a song appears on. "
        "Use 'album' to get the tracklist and release year for an album. "
        "Call with no parameters to list all studio albums. "
        "Covers all studio releases from The White Tape (1984) through Sigma Oasis (2020)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Song name to look up, e.g. 'Kill Devil Falls', 'Maze', 'First Tube'",
            },
            "album": {
                "type": "string",
                "description": "Album name to look up, e.g. 'Rift', 'Farmhouse', 'Joy'",
            },
        },
        "required": [],
    },
}


def search_discography(
    song: Optional[str] = None,
    album: Optional[str] = None,
) -> dict:
    """
    Search the Phish studio discography.

    If `song` is provided, returns matching tracks across all albums.
    If `album` is provided (and `song` is not), returns matching album records.
    If neither is provided, returns a title/year index of all albums.

    When both are provided, `song` takes precedence.
    """
    if song is not None:
        query = song.strip().lower()
        if not query:
            return {"matches": [], "source": "discography"}
        matches = []
        for record in DISCOGRAPHY:
            for track in record["songs"]:
                if query in track.lower():
                    matches.append({
                        "song": track,
                        "album": record["title"],
                        "year": record["year"],
                    })
        return {"matches": matches, "source": "discography"}

    if album is not None:
        query = album.strip().lower()
        if not query:
            return {"albums": [], "source": "discography"}
        albums = [r for r in DISCOGRAPHY if query in r["title"].lower()]
        return {"albums": albums, "source": "discography"}

    # No params — return index of all albums
    index = [{"title": r["title"], "year": r["year"]} for r in DISCOGRAPHY]
    return {"albums": index, "source": "discography"}
