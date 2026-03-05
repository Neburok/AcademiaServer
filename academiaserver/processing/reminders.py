import re
from datetime import datetime
from dateparser.search import search_dates


def extract_hour(text):

    pattern = r"a las (\d{1,2})(?::(\d{2}))?\s?(am|pm)?"
    match = re.search(pattern, text.lower())

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    period = match.group(3)

    if period == "pm" and hour < 12:
        hour += 12

    if period == "am" and hour == 12:
        hour = 0

    return hour, minute


def extract_date(text):

    result = search_dates(
        text,
        languages=["es"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
    )

    if result:
        return result[0][1]

    return None


def build_datetime(date_obj, hour_tuple):

    if not date_obj:
        return None

    if not hour_tuple:
        return date_obj

    hour, minute = hour_tuple

    return datetime(
        year=date_obj.year,
        month=date_obj.month,
        day=date_obj.day,
        hour=hour,
        minute=minute
    )


def parse_reminder(text):

    date_obj = extract_date(text)
    hour_tuple = extract_hour(text)

    dt = build_datetime(date_obj, hour_tuple)

    if not dt:
        return None

    return {
        "datetime": dt.isoformat()
    }