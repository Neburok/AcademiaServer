import dateparser
from datetime import datetime
from dateparser.search import search_dates


def extract_datetime(text: str):
    result = search_dates(
        text,
        languages=["es"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
    )

    if result:
        return result[0][1]  # devuelve el datetime detectado

    return None


tests = [
    "recuérdame mañana a las 7 revisar el proyecto",
    "tengo junta el viernes a las 3 pm",
    "recordar llamar a Juan en 2 horas",
    "tarea el 15 de marzo a las 10",
    "mañana tengo clase"
]

for t in tests:
    print("Texto:", t)
    print("Detectado:", extract_datetime(t))
    print("-" * 40)