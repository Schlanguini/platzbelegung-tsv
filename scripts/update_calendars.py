import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ics import Calendar, Event
import re

BASE_URL = "https://www.fussball.de/verein/tsv-wentorf-sandesneben-schleswig-holstein/-/id/00ES8GN8JC00006CVV0AG08LVUPGND5I"

FIELDS = {
    "KR": "Kunstrasenplatz, Wentorf Platz 1 (KR), Sparrbucht 4, 23898 Wentorf A.S.",
    "R1": "Rasenplatz, Wentorf Platz 2, Sparrbucht 4, 23898 Wentorf A.S.",
    "S1": "Rasenplatz, Schönberg Platz 1, Jägerstr. 5, 22929 Schönberg"
}

BASE_URL = "https://www.fussball.de/verein/tsv-wentorf-sandesneben-schleswig-holstein/-/id/00ES8GN8JC00006CVV0AG08LVUPGND5I"

def fetch_teams():
    r = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "lxml")

    links = soup.find_all("a")

    team_urls = []

    for a in links:
        href = a.get("href", "")
        if "/mannschaft/" in href:
            team_urls.append("https://www.fussball.de" + href)

    return list(set(team_urls))

def fetch_matches_from_team(url):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "lxml")

    matches = []

    rows = soup.find_all("tr")

    for row in rows:
        text = row.get_text(" ", strip=True)

        if "gegen" in text:
            matches.append(text)

    return matches


def main():
    team_urls = fetch_teams()

    all_matches = []

    for url in team_urls:
        all_matches.extend(fetch_matches_from_team(url))

    calendars = build_calendars(all_matches)
    save(calendars)


import re

def parse_team(team_text: str):
    t = team_text.lower()

    # Altersklasse erkennen
    age = None
    if "g" in t and "jun" in t:
        age = "G"
    elif "f" in t:
        age = "F"
    elif "e" in t:
        age = "E"
    elif "d" in t:
        age = "D"
    elif "c" in t:
        age = "C"
    elif "b" in t:
        age = "B"
    elif "a" in t:
        age = "A"
    elif "herr" in t:
        age = "Herren"
    elif "ü40" in t:
        age = "Ü40"
    elif "ü50" in t:
        age = "Ü50"
    elif "alt" in t:
        age = "Altherren"

    # Teamnummer erkennen (1, 2, II, III etc.)
    match = re.search(r"(?:\s|^)(\d+|ii|iii|iv|v)(?:\s|$)", t)
    team_nr = match.group(1).upper() if match else ""

    if age in ["Herren", "Ü40", "Ü50", "Altherren"]:
        return age

    if team_nr:
        return f"{age}{team_nr}"
    else:
        return f"{age}"


def get_category(team_text: str):
    t = team_text.lower()

    if "herr" in t:
        return "Herren", "blue"

    if "ü40" in t or "ü50" in t or "alten" in t:
        return "Altherren", "orange"

    if any(x in t for x in ["g-", "f-", "e-", "d-", "c-", "b-", "a-"]):
        return "Jugend", "green"

    return "Sonstiges", "gray"


def get_duration(team_text):
    t = team_text.lower()

    if "g-" in t or "g-junior" in t:
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
    if "ü40" in t or "ü50" in t:
        return 85

    return 90


def classify_field(text):
    t = text.lower()

    if "kunstrasen" in t:
        return "KR"
    if "platz 2" in t:
        return "R1"
    if "schönberg" in t:
        return "S1"

    return None


def build_calendars(matches):
    calendars = {"KR": Calendar(), "R1": Calendar(), "S1": Calendar()}

    now = datetime.now()
    start = now - timedelta(days=730)
    end = now + timedelta(days=730)

    for m in all_matches:
        field = classify_field(m)
        if not field:
            continue

        # Dummy Zeit (wird aus Detailseite später verbessert)
        match_time = now + timedelta(days=1)

        duration = get_duration(m)

        team_name = parse_team(m)

        title = f"({team_name}) {m}"

        team_type, color = get_category(m)

        e = Event()
        e.name = f"({team_type}) {title}"
        e.begin = match_time
        e.duration = timedelta(minutes=duration)

        # Outlook Kategorie (wichtig für Farben)
        e.categories = [team_type]
        e.description = f"""
        Kategorie: {team_type}
        Anstoß: {match_time}
        Spiel: {title}
        Quelle: FUSSBALL.DE
        """

        calendars[field].events.add(e)

    return calendars


def save(calendars):
    import os
    os.makedirs("output", exist_ok=True)

    with open("output/wentorf_kunstrasen.ics", "w", encoding="utf-8") as f:
        f.write(calendars["KR"].serialize())

    with open("output/wentorf_rasen.ics", "w", encoding="utf-8") as f:
        f.write(calendars["R1"].serialize())

    with open("output/schoenberg_rasen.ics", "w", encoding="utf-8") as f:
        f.write(calendars["S1"].serialize())


def main():
    team_urls = fetch_teams()

    all_matches = []

    for url in team_urls:
        all_matches.extend(fetch_matches_from_team(url))

    calendars = build_calendars(all_matches)
    save(calendars)


if __name__ == "__main__":
    main()
