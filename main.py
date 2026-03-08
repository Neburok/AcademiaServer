import argparse

from academiaserver.core import (
    get_daily_digest,
    get_idea_by_id,
    list_ideas,
    reembed_notas,
    save_idea,
    search_ideas,
)
from academiaserver.logger import show_logs
from academiaserver.processing.pipeline import process_note


def main():
    parser = argparse.ArgumentParser(description="AcademiaServer - Mitzlia")
    subparsers = parser.add_subparsers(dest="command")

    save_parser = subparsers.add_parser("save", help="Guardar nueva nota")
    save_parser.add_argument("--content", required=True, help="Contenido de la nota")
    save_parser.add_argument("--title", required=False, help="Titulo opcional")

    get_parser = subparsers.add_parser("get", help="Obtener nota por ID")
    get_parser.add_argument("--id", required=True, help="ID de la nota")

    search_parser = subparsers.add_parser("search", help="Buscar notas")
    search_parser.add_argument("query", type=str)
    search_parser.add_argument(
        "--backend",
        choices=["keyword", "semantic"],
        default="keyword",
        help="Backend de busqueda",
    )

    subparsers.add_parser("list", help="Listar archivos de notas")
    subparsers.add_parser("log", help="Mostrar logs")
    subparsers.add_parser("digest", help="Generar digest diario")
    subparsers.add_parser("reembed", help="Generar embeddings para notas sin vector")

    args = parser.parse_args()

    if args.command == "save":
        note = process_note(args.content, source="cli")
        if args.title:
            note["title"] = args.title
        saved = save_idea(note)
        print(f"Nota guardada con ID: {saved['id']}")
    elif args.command == "list":
        ideas = list_ideas()
        if not ideas:
            print("No hay ideas guardadas.")
        else:
            for idea in ideas:
                print(f"{idea['id']} - {idea.get('title', '(sin título)')}")
    elif args.command == "log":
        logs = show_logs()
        print(logs if logs else "No hay logs aun.")
    elif args.command == "get":
        idea = get_idea_by_id(args.id)
        print(idea if idea else "Idea no encontrada.")
    elif args.command == "search":
        results = search_ideas(args.query, backend=args.backend)
        if not results:
            print("No se encontraron ideas.")
        else:
            for idea in results:
                print(f"{idea['id']} - {idea['title']}")
    elif args.command == "digest":
        digest = get_daily_digest()
        print(digest["text"])
    elif args.command == "reembed":
        print("Generando embeddings para notas sin vector...")
        stats = reembed_notas()
        print(f"Total pendientes: {stats['total']}")
        print(f"Procesadas:       {stats['procesadas']}")
        if stats["fallidas"]:
            print(f"Fallidas (Ollama no disponible): {stats['fallidas']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
