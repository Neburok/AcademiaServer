"""
reset_db.py — Reinicia la BD de Mitzlia desde cero.

ADVERTENCIA: Borra TODOS los datos (notas, recordatorios, actividad).
Solo usar cuando se quiera empezar con una base de datos en blanco.

Uso:
    python reset_db.py
"""
import os
import sys

from academiaserver.config import DB_PATH


def main() -> None:
    print()
    print("=" * 55)
    print("  reset_db.py — Reinicio de base de datos de Mitzlia")
    print("=" * 55)
    print()
    print("  ⚠️  ADVERTENCIA: Este script borrará TODOS los datos.")
    print(f"  Base de datos: {DB_PATH}")
    print()
    respuesta = input("  Escribe 'CONFIRMAR' para continuar: ").strip()

    if respuesta != "CONFIRMAR":
        print()
        print("  Operación cancelada. No se modificó nada.")
        sys.exit(0)

    print()

    # 1. Eliminar la BD actual
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  ✅ BD eliminada: {DB_PATH}")
    else:
        print(f"  ℹ️  BD no encontrada (ya estaba limpia): {DB_PATH}")

    # 2. Recrear el esquema con Alembic
    print("  ⏳ Recreando esquema con alembic upgrade head...")
    exit_code = os.system("alembic upgrade head")
    if exit_code != 0:
        print()
        print("  ❌ Error al ejecutar alembic upgrade head.")
        print("     Verifica que Alembic está instalado y que alembic.ini existe.")
        sys.exit(1)

    print()
    print("  ✅ Esquema recreado correctamente.")
    print()
    print("  🟢 Mitzlia lista para empezar desde cero.")
    print()


if __name__ == "__main__":
    main()
