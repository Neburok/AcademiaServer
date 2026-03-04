import argparse
from academiaserver.core import save_idea, list_ideas
from academiaserver.logger import show_logs


def main():
    parser = argparse.ArgumentParser(
        description="AcademiaServer - Sistema Académico Autónomo"
    )

    subparsers = parser.add_subparsers(dest="command")

    # Comando save
    save_parser = subparsers.add_parser("save", help="Guardar nueva idea")
    save_parser.add_argument("text", nargs="+", help="Texto de la idea")

    # Comando list
    subparsers.add_parser("list", help="Listar ideas guardadas")

    # Comando log
    subparsers.add_parser("log", help="Mostrar logs")

    args = parser.parse_args()

    if args.command == "save":
        idea_text = " ".join(args.text)
        save_idea(idea_text)
        print("Idea guardada correctamente.")

    elif args.command == "list":
        list_ideas()

    elif args.command == "log":
        show_logs()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()