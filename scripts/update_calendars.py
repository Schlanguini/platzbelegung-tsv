import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ics import Calendar, Event
from urllib.parse import urljoin
import json
import re

BASE_URL = "https://www.fussball.de/verein/tsv-wentorf-sandesneben-schleswig-holstein/-/id/00ES8GN8JC00006CVV0AG08LVUPGND5I"

FIELDS = {
    "KR": "Kunstrasenplatz, Wentorf Platz 1 (KR), Sparrbucht 4, 23898 Wentorf A.S.",
    "R1": "Rasenplatz, Wentorf Platz 2, Sparrbucht 4, 23898 Wentorf A.S.",
    "S1": "Rasenplatz, Schönberg Platz 1, Jägerstr. 5, 22929 Schönberg"
}


# -----------------------------
# TEAMS
# -----------------------------
def fetch_teams():
    r = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "lxml")

    teams = []

    for a in soup.select("a"):
        href = a.get("href", "")

        if "mannschaft" in href:
            teams.append(urljoin("https://www.fussball.de", href))

    return list(set(teams))


# -----------------------------
# SPIELE
# -----------------------------
def fetch_matches_from_team(team_url):

    # Team-ID aus URL extrahieren
    team_id = team_url.split("team-id/")[-1] if "team-id/" in team_url else None

    if not team_id:
        return []

    api_url = f"https://www.fussball.de/ajax.teamFixtures/{team_id}"

    try:
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()

        matches = []

        for m in data.get("matches", []):
            matches.append(m)

        return matches

    except:
        return []

# -----------------------------
# HOME FILTER (robust)
# -----------------------------
def is_home_match(match):

    try:
        home = (
            match.get("homeTeam", {}).get("name")
            or match.get("home", {}).get("name")
            or ""
        ).lower()

        # robust statt nur "wentorf"
        return any(x in home for x in ["wentorf", "sg wentorf", "sandesneben"])

    except:
        return False


# -----------------------------
# DATUM PARSEN
# -----------------------------
def parse_date(match):

    raw = match.get("matchDate") or match.get("date") or ""

    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw.replace("Z", ""))
    except:
        return None


# -----------------------------
# PLATZ
# -----------------------------
def classify_field(text):

    t = text.lower()

    if "schönberg" in t:
        return "S1"
    if "platz 2" in t:
        return "R1"
    return "KR"


# -----------------------------
# KALENDER
# -----------------------------
def build_calendars(matches):

    calendars = {
        "KR": Calendar(),
        "R1": Calendar(),
        "S1": Calendar()
    }

    for m in matches:

        if not is_home_match(m):
            continue

        try:
            home = (
                m.get("homeTeam", {}).get("name")
                or m.get("home", {}).get("name")
                or "Heimteam"
            )

            away = (
                m.get("awayTeam", {}).get("name")
                or m.get("away", {}).get("name")
                or "Gast"
            )

            match_time = parse_date(m)
            if not match_time:
                continue

            field = classify_field(home + " " + away)

            e = Event()
            e.name = f"{home} - {away}"
            e.begin = match_time
            e.duration = timedelta(minutes=90)
            e.categories = ["Heimspiel"]
            e.description = "Heimspiel TSV Wentorf"

            calendars[field].events.add(e)

        except:
            continue

    return calendars


# -----------------------------
# SAVE
# -----------------------------
def save(calendars):

    import os
    os.makedirs("output", exist_ok=True)

    with open("output/wentorf_kunstrasen.ics", "w", encoding="utf-8") as f:
        f.write(calendars["KR"].serialize())

    with open("output/wentorf_rasen.ics", "w", encoding="utf-8") as f:
        f.write(calendars["R1"].serialize())

    with open("output/schoenberg_rasen.ics", "w", encoding="utf-8") as f:
        f.write(calendars["S1"].serialize())


# -----------------------------
# MAIN
# -----------------------------
def main():

    team_urls = fetch_teams()

    all_matches = []

    for url in team_urls:
        all_matches.extend(fetch_matches_from_team(url))

    calendars = build_calendars(all_matches)
    save(calendars)


if __name__ == "__main__":
    main()
