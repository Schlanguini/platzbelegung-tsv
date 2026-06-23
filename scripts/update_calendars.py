import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ics import Calendar, Event
from urllib.parse import urljoin
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

    team_urls = []

    for a in soup.find_all("a"):
        href = a.get("href", "")

        if "/mannschaft/" in href:
            team_urls.append(urljoin("https://www.fussball.de", href))

    return list(set(team_urls))


# -----------------------------
# SPIELE
# -----------------------------
def fetch_matches_from_team(url):

    if not url or not url.startswith("http"):
        return []

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "lxml")

    matches = []

    for row in soup.find_all("tr"):
        text = row.get_text(" ", strip=True)

        if "gegen" in text:
            matches.append(text)

    return matches


# -----------------------------
# TEAM NAME
# -----------------------------
def parse_team(text):
    t = text.lower()

    match = re.search(r"(g|f|e|d|c|b|a)[-\s]?(\d+|ii|iii|iv)?", t)

    if match:
        base = match.group(1).upper()
        nr = match.group(2)

        if nr:
            nr = nr.replace("ii", "2").replace("iii", "3").replace("iv", "4")
            return f"{base}{nr}"
        return base

    if "herr" in t:
        return "Herren"

    if "ü40" in t:
        return "Ü40"

    if "ü50" in t:
        return "Ü50"

    return "Team"


# -----------------------------
# PLATZ
# -----------------------------
def classify_field(text):
    t = text.lower()

    if "schönberg" in t:
        return "S1"
    if "platz 2" in t:
        return "R1"
    if "kunstrasen" in t:
        return "KR"

    return "KR"


# -----------------------------
# DAUER
# -----------------------------
def get_duration(text):
    t = text.lower()

    if "g-" in t:
        return 180
    if "f-" in t:
        return 50
    if "e-" in t:
        return 60
    if "d-" in t:
        return 70
    if "c-" in t:
        return 85
    if "b-" in t:
        return 95
    if "a-" in t:
        return 105
    if "herr" in t:
        return 105

    return 90


# -----------------------------
# KALENDER
# -----------------------------
def build_calendars(matches):

    calendars = {
        "KR": Calendar(),
        "R1": Calendar(),
        "S1": Calendar()
    }

    now = datetime.now()

    for m in matches:

        field = classify_field(m)
        team = parse_team(m)

        start = now + timedelta(days=1)

        e = Event()
        e.name = f"({team}) {m}"
        e.begin = start
        e.duration = timedelta(minutes=get_duration(m))
        e.categories = [team]
        e.description = f"{m} | Quelle: FUSSBALL.DE"

        calendars[field].events.add(e)

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
