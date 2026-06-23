import requests
from datetime import datetime, timedelta
from ics import Calendar, Event

# -----------------------------
# KONFIGURATION
# -----------------------------
CLUB_URL = "https://www.fussball.de/ajax.clubFixtures"  # interne FUSSBALL.DE API (funktioniert i.d.R.)
CLUB_ID = "00ES8GN8JC00006CVV0AG08LVUPGND5I"

FIELDS = {
    "KR": "Kunstrasenplatz, Wentorf Platz 1 (KR), Sparrbucht 4, 23898 Wentorf A.S.",
    "R1": "Rasenplatz, Wentorf Platz 2, Sparrbucht 4, 23898 Wentorf A.S.",
    "S1": "Rasenplatz, Schönberg Platz 1, Jägerstr. 5, 22929 Schönberg"
}

def fetch_matches():
    payload = {
        "clubId": CLUB_ID,
        "onlyHomeMatches": True
    }
    r = requests.get(CLUB_URL, params=payload)
    r.raise_for_status()
    return r.json()

def get_match_duration(team_name: str):
    t = team_name.lower()

    if "g-" in t or "g-junior" in t:
        return 3 * 60
    if "f-" in t or "f-junior" in t:
        return 50
    if "e-" in t or "e-junior" in t:
        return 60
    if "d-" in t or "d-junior" in t:
        return 70
    if "c-" in t or "c-junior" in t:
        return 85
    if "b-" in t or "b-junior" in t:
        return 95
    if "a-" in t or "a-junior" in t:
        return 105
    if "herr" in t:
        return 105
    if "ü40" in t or "ü50" in t or "alten" in t:
        return 85

    return 90  # fallback

def classify_field(match):
    place = match.get("location", "").lower()

    if "kunstrasen" in place:
        return "KR"
    if "wentorf platz 2" in place or "rasenplatz wentorf" in place:
        return "R1"
    if "schönberg" in place:
        return "S1"

    return None

def build_calendars(matches):
    calendars = {
        "KR": Calendar(),
        "R1": Calendar(),
        "S1": Calendar()
    }

    now = datetime.now()
    start_range = now - timedelta(days=730)
    end_range = now + timedelta(days=730)

    for m in matches:
        field = classify_field(m)
        if not field:
            continue

        match_time = datetime.fromisoformat(m["kickoff"])

        if match_time < start_range or match_time > end_range:
            continue

        duration = get_match_duration(m.get("homeTeam", ""))

        title = f"({m.get('homeTeamShort','')}) {m['homeTeam']} - {m['awayTeam']}"

        event = Event()
        event.name = title
        event.begin = match_time
        event.duration = timedelta(minutes=duration)

        event.description = f"""
Wettbewerb: {m.get('competition','')}
Anstoß: {match_time}

Heimteam: {m['homeTeam']}
Gastteam: {m['awayTeam']}

Spielort: {m.get('location','')}

Quelle: FUSSBALL.DE
"""

        calendars[field].events.add(event)

    return calendars

def save(calendars):
    calendars["KR"].serialize().write("output/wentorf_kunstrasen.ics")
    calendars["R1"].serialize().write("output/wentorf_rasen.ics")
    calendars["S1"].serialize().write("output/schoenberg_rasen.ics")

def main():
    matches = fetch_matches()
    calendars = build_calendars(matches)
    save(calendars)

if __name__ == "__main__":
    main()
