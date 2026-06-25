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

            # Filter: nur +- 1 Jahr
            now = datetime.now()
            one_year = timedelta(days=365)
            if not (now - one_year <= start <= now + one_year):
                continue

            text = (
                str(ev.get("LOCATION", ""))
                + " "
                + str(ev.get("DESCRIPTION", ""))
            )

            field = classify_field(text)

            e = Event()

            # Mannschaftstyp (z. B. "D2-Junioren")
            team = ev.team_name

            # Heimverein immer fix
            HOME_TEAM_NAME = "SGWSS"

            # Gegner aus SUMMARY extrahieren
            summary = str(ev.get("SUMMARY", ""))

            # DFBnet-Format: "<Gast> - <Heim>"
            if "-" in summary:
                guest, home = summary.split("-", 1)
                guest = guest.strip()
            else:
                guest = summary.strip()

            # Titel setzen: (Team) SGWSS - Gast
            e.name = f"({team}) {HOME_TEAM_NAME} - {guest}"

            e.begin = start

            # Dauer anhand TEAM_DURATIONS
            duration_minutes = TEAM_DURATIONS.get(team, 120)
            e.duration = timedelta(minutes=duration_minutes)

            e.location = str(ev.get("LOCATION", ""))
            e.description = str(ev.get("DESCRIPTION", ""))

            calendars[field].events.add(e)

        except Exception as ex:
            print("Fehler beim Verarbeiten:", ex)

    return calendars
