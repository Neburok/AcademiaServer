import sys
from academiaserver.core import save_idea

def show_help():
    print("Uso:")
    print('  python main.py "Texto de la idea académica"')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    else:
        idea_text = " ".join(sys.argv[1:])
        save_idea(idea_text)
        print("Idea guardada correctamente.")