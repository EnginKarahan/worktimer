from datetime import date
from django.conf import settings


def get_holidays_for_year(year: int, federal_state: str | None = None) -> list[tuple[date, str]]:
    """Gibt Feiertage für ein Jahr zurück. Nutzt workalendar."""
    try:
        from workalendar.europe import Germany
        # State-specific calendars
        state_map = {
            "BY": "workalendar.europe.germany.Bavaria",
            "BE": "workalendar.europe.germany.Berlin",
            "BB": "workalendar.europe.germany.Brandenburg",
            "BW": "workalendar.europe.germany.BadenWurttemberg",
            "HB": "workalendar.europe.germany.Bremen",
            "HH": "workalendar.europe.germany.Hamburg",
            "HE": "workalendar.europe.germany.Hesse",
            "MV": "workalendar.europe.germany.MecklenburgVorpommern",
            "NI": "workalendar.europe.germany.LowerSaxony",
            "NW": "workalendar.europe.germany.NorthRhineWestphalia",
            "RP": "workalendar.europe.germany.RhinelandPalatinate",
            "SL": "workalendar.europe.germany.Saarland",
            "SN": "workalendar.europe.germany.Saxony",
            "ST": "workalendar.europe.germany.SaxonyAnhalt",
            "SH": "workalendar.europe.germany.SchleswigHolstein",
            "TH": "workalendar.europe.germany.Thuringia",
        }
        fs = federal_state or getattr(settings, "FEDERAL_STATE", "BY")
        module_path = state_map.get(fs)
        if module_path:
            parts = module_path.rsplit(".", 1)
            mod = __import__(parts[0], fromlist=[parts[1]])
            cal_class = getattr(mod, parts[1])
            cal = cal_class()
        else:
            cal = Germany()
        return cal.holidays(year)
    except Exception:
        return []


def is_holiday(d: date, federal_state: str | None = None) -> bool:
    holidays = get_holidays_for_year(d.year, federal_state)
    return any(h[0] == d for h in holidays)


def is_working_day(d: date, federal_state: str | None = None) -> bool:
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return not is_holiday(d, federal_state)
