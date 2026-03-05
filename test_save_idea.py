from academiaserver.core import save_idea

note = {
    "content": "Recuérdame la cita con el dentista el viernes a las 12 pm",
    "type": "recordatorio",
    "tags": ["salud"],
    "metadata": {
        "event": "cita con el dentista",
        "datetime": "2026-03-07T12:00:00"
    },
    "source": "test"
}

result = save_idea(note)

print("Nota guardada:")
print(result)