from academiaserver.processing.pipeline import process_note

tests = [
    "Recuérdame la cita con el dentista el viernes a las 12 pm",
    "Idea para mejorar la clase de SEM con aprendizaje basado en problemas",
    "Recordar revisar los resultados del experimento mañana a las 8",
    "Apunte: revisar la ecuación de difusión térmica"
]

for t in tests:

    print("Mensaje:")
    print(t)

    note = process_note(t, source="test")

    print("Resultado:")
    print(note)

    print("-" * 50)