import json
import requests

from datetime import datetime, timedelta
from ics import Calendar, Event
from icalendar import Calendar as ICalCalendar


FIELDS = {
    "KR": "Kunstrasenplatz, Wentorf Platz 1 (KR), Sparrbucht 4, 23898 Wentorf A.S.",
    "R1": "Rasenplatz, Wentorf Platz 2, Sparrbucht 4, 23898 Wentorf A.S.",
    "S1": "Rasenplatz, Schönberg Platz 1, Jägerstr. 5, 22929 Schönberg"
}


HOME_CLUB = "TSV Wentorf"


def load_team_calendars():

    with open("team_calendars.json", encoding="utf-8") as f:
        calendars = json.load(f)

    events = []

    for team_name, url in calendars.items():

        url = url.replace("webcal://", "https://")

        print(f"\nLade Kalender: {team_name}")

        try:

            response = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            response.raise_for_status()

            cal = ICalCalendar.from_ical(response.content)

            count = 0

            for component in cal.walk():

                if component.name == "VEVENT":
                    component.team_name = team_name
                    events.append(component)
                    count += 1

            print(f"Gefundene Termine: {count}")

        except Exception as e:
            print(f"Fehler bei {team_name}: {e}")

    return events


def is_real_match(event):

    summary = str(
        event.get("SUMMARY", "")
    ).lower()

    blacklist = [
        "training",
        "trainingsbetrieb",
        "trainer",
        "veranstaltung",
        "event",
        "besprechung",
        "sitzung",
        "arbeitseinsatz",
        "vorstand",
        "versammlung"
    ]

    return not any(word in summary for word in blacklist)


def is_home_match(event):

    location = str(
        event.get("LOCATION", "")
    ).lower()

    home_keywords = [
        "wentorf",
        "schönberg",
        "schoenberg"
    ]

    return any(
        keyword in location
        for keyword in home_keywords
    )


def classify_field(text):

    t = text.lower()

    if "schönberg" in t or "schoenberg" in t:
        return "S1"

    if "platz 2" in t:
        return "R1"

    if "(kr)" in t:
        return "KR"

    if "kunstrasen" in t:
        return "KR"

    return "R1"


def build_calendars(events):

    calendars = {
        "KR": Calendar(),
        "R1": Calendar(),
        "S1": Calendar()
    }

    for ev in events:

        if not is_real_match(ev):
            continue

        if not is_home_match(ev):
            continue

        try:

            start = ev.decoded("DTSTART")

            text = (
                str(ev.get("LOCATION", ""))
                + " "
                + str(ev.get("DESCRIPTION", ""))
            )

            print(
            "SPIELORT:",
            str(ev.get("LOCATION", ""))
            )

            field = classify_field(text)

            e = Event()

            e.name = str(
                ev.get("SUMMARY", "Heimspiel")
            )

            e.begin = start

            e.duration = timedelta(hours=2)

            e.location = str(
                ev.get("LOCATION", "")
            )

            e.description = str(
                ev.get("DESCRIPTION", "")
            )

            calendars[field].events.add(e)

        except Exception as ex:
            print("Fehler beim Verarbeiten:", ex)

    return calendars


def save(calendars):

    import os

    os.makedirs("output", exist_ok=True)

    with open(
        "output/wentorf_kunstrasen.ics",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(calendars["KR"].serialize())

    with open(
        "output/wentorf_rasen.ics",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(calendars["R1"].serialize())

    with open(
        "output/schoenberg_rasen.ics",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(calendars["S1"].serialize())


def main():

    events = load_team_calendars()

    print("\n===================================")
    print("GESAMT TERMINE:", len(events))
    print("===================================\n")

    print("DEBUG AUSGABE ERSTE TERMINE\n")

    for event in events[:15]:

        print("TEAM:", getattr(event, "team_name", "unbekannt"))
        print("SUMMARY:", event.get("SUMMARY"))
        print("LOCATION:", event.get("LOCATION"))
        print("DESCRIPTION:", event.get("DESCRIPTION"))
        print("--------------------------------")

    calendars = build_calendars(events)

    total_events = sum(
        len(cal.events)
        for cal in calendars.values()
    )

    print("\n===================================")
    print("HEIMSPIELE:", total_events)
    print("KR:", len(calendars["KR"].events))
    print("R1:", len(calendars["R1"].events))
    print("S1:", len(calendars["S1"].events))
    print("===================================\n")

    save(calendars)


if __name__ == "__main__":
    main()
