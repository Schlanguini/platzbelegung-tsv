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

def get_html():
    r = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def parse_matches(html):
    soup = BeautifulSoup(html, "lxml")

    matches = []

    # FUSSBALL.DE Struktur: viele Links + Tabellenzeilen
    rows = soup.find_all(text=re.compile("gegen|:"))

    for row in rows:
        text = row.strip()

        if "gegen" not in text:
            continue

        matches.append(text)

    return matches


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

    for m in matches:
        field = classify_field(m)
        if not field:
            continue

        # Dummy Zeit (wird aus Detailseite später verbessert)
        match_time = now + timedelta(days=1)

        duration = get_duration(m)

        title = f"{m}"

        e = Event()
        e.name = title
        e.begin = match_time
        e.duration = timedelta(minutes=duration)
        e.description = m

        calendars[field].events.add(e)

    return calendars


def save(calendars):
    calendars["KR"].serialize().write("output/wentorf_kunstrasen.ics")
    calendars["R1"].serialize().write("output/wentorf_rasen.ics")
    calendars["S1"].serialize().write("output/schoenberg_rasen.ics")


def main():
    html = get_html()
    matches = parse_matches(html)
    calendars = build_calendars(matches)
    save(calendars)


if __name__ == "__main__":
    main()
