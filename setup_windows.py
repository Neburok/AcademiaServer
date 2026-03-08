"""
setup_windows.py — Configuración de accesos directos de Mitzlia en Windows.

Crea en el Escritorio:
  • "Iniciar Mitzlia.lnk"  → start_mitzlia.bat  (ícono de Mitzlia)
  • "Detener Mitzlia.lnk"  → stop_mitzlia.bat   (ícono de Mitzlia)

Requisitos:
  pip install pillow pywin32
"""

import os
import sys
from pathlib import Path


def convertir_a_ico(ruta_imagen: Path, ruta_ico: Path):
    try:
        from PIL import Image
    except ImportError:
        print("  ERROR: Pillow no está instalado. Ejecuta: pip install pillow")
        sys.exit(1)

    img = Image.open(ruta_imagen).convert("RGBA")
    img.save(
        ruta_ico,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print(f"  Ícono generado: {ruta_ico}")


def crear_acceso_directo(nombre: str, destino: Path, icono: Path, directorio: Path):
    try:
        import win32com.client
    except ImportError:
        print("  ERROR: pywin32 no está instalado. Ejecuta: pip install pywin32")
        sys.exit(1)

    escritorio = Path.home() / "Desktop"
    ruta_lnk = escritorio / f"{nombre}.lnk"

    shell = win32com.client.Dispatch("WScript.Shell")
    acceso = shell.CreateShortCut(str(ruta_lnk))
    acceso.TargetPath = str(destino)
    acceso.WorkingDirectory = str(directorio)
    acceso.IconLocation = str(icono)
    acceso.Description = nombre
    acceso.Save()

    print(f"  Acceso directo creado: {ruta_lnk}")


def main():
    base = Path(__file__).parent.resolve()
    ruta_imagen = base / "assets" / "mitzlia_v0.jpeg"
    ruta_ico = base / "assets" / "mitzlia.ico"

    if not ruta_imagen.exists():
        print(f"ERROR: No se encontró la imagen en {ruta_imagen}")
        sys.exit(1)

    print("\n  Configurando Mitzlia en Windows...")
    print()

    print("  [1/3] Convirtiendo imagen a .ico...")
    convertir_a_ico(ruta_imagen, ruta_ico)

    print("  [2/3] Creando acceso directo 'Iniciar Mitzlia'...")
    crear_acceso_directo(
        nombre="Iniciar Mitzlia",
        destino=base / "start_mitzlia.bat",
        icono=ruta_ico,
        directorio=base,
    )

    print("  [3/3] Creando acceso directo 'Detener Mitzlia'...")
    crear_acceso_directo(
        nombre="Detener Mitzlia",
        destino=base / "stop_mitzlia.bat",
        icono=ruta_ico,
        directorio=base,
    )

    print()
    print("  Listo. Revisa el Escritorio.")
    print()


if __name__ == "__main__":
    main()
