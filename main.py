import argparse
from academiaserver.core import save_idea, list_ideas, search_ideas
from academiaserver.logger import show_logs
from academiaserver.core import get_idea_by_id
from academiaserver.core import search_ideas


def main():
    parser = argparse.ArgumentParser(
        description="AcademiaServer - Sistema Académico Autónomo"
    )

    subparsers = parser.add_subparsers(dest="command")

    # Comando save
    save_parser = subparsers.add_parser("save", help="Guardar nueva idea")
    save_parser.add_argument("--title", required=True, help="Título de la idea")
    save_parser.add_argument("--content", required=True, help="Contenido de la idea")

    get_parser = subparsers.add_parser("get", help="Obtener idea por ID")
    get_parser.add_argument("--id", required=True, help="ID de la idea")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query", type=str)
   # save_parser = subparsers.add_parser("save", help="Guardar nueva idea")
   # save_parser.add_argument("text", nargs="+", help="Texto de la idea")

    # Comando list
    subparsers.add_parser("list", help="Listar ideas guardadas")

    # Comando log
    subparsers.add_parser("log", help="Mostrar logs")

    args = parser.parse_args()

    if args.command == "save":
        idea = save_idea(args.title, args.content)
        print(f"Idea guardada con ID: {idea.id}")

    elif args.command == "list":
        ideas = list_ideas()
        if not ideas:
            print("No hay ideas guardadas.")
        else:
            for idea in ideas:
                print(idea)

    elif args.command == "log":
        logs = show_logs()
        if not logs:
            print("No hay logs aún.")
        else:
            print(logs)
    
    elif args.command == "get":
        idea = get_idea_by_id(args.id)
        if not idea:
            print("Idea no encontrada.")
        else:
            print(idea)

    elif args.command == "search":
        results = search_ideas(args.query)
        if not results:
            print("No se encontraron ideas.")
        else:
            for idea in results:
                print(f"{idea['id']} - {idea['title']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()