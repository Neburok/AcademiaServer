"""DocumentWriter — guarda archivos .md y .tex generados por los agentes educativos."""
import unicodedata
import re
from datetime import datetime
from pathlib import Path

from academiaserver.config import OUTPUTS_DIR


def _slugify(text: str, max_chars: int = 40) -> str:
    """Convierte texto a slug ASCII seguro para nombres de archivo.

    Proceso:
    1. Normaliza a NFD (separa letras de tildes)
    2. Elimina diacríticos (categoria Mn = Mark, Nonspacing)
    3. Convierte a minúsculas
    4. Reemplaza secuencias de caracteres no alfanuméricos por '_'
    5. Recorta guiones bajos extremos
    6. Limita a max_chars
    """
    nfkd = unicodedata.normalize("NFD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    lower = ascii_text.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lower).strip("_")
    return slug[:max_chars]


class DocumentWriter:
    """Guarda contenido Markdown o LaTeX en disco con nombre estructurado.

    Nombre de archivo: ``YYYYMMDD_HHMMSS_<task_type>_<slug>.<ext>``
    """

    def __init__(self, outputs_dir: str | None = None):
        self._outputs_dir = Path(outputs_dir or OUTPUTS_DIR)

    def _ensure_dir(self) -> None:
        """Crea el directorio de salida si no existe."""
        self._outputs_dir.mkdir(parents=True, exist_ok=True)

    def _build_filename(self, task_type: str, title: str, ext: str) -> str:
        """Genera el nombre de archivo con timestamp y slug del título."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = _slugify(title)
        return f"{timestamp}_{task_type}_{slug}{ext}"

    def save_markdown(self, content: str, task_type: str, title: str) -> Path:
        """Guarda *content* como archivo ``.md`` y retorna el Path resultante."""
        self._ensure_dir()
        filename = self._build_filename(task_type, title, ".md")
        path = self._outputs_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def save_tex(self, content: str, task_type: str, title: str) -> Path:
        """Guarda *content* como archivo ``.tex`` y retorna el Path resultante."""
        self._ensure_dir()
        filename = self._build_filename(task_type, title, ".tex")
        path = self._outputs_dir / filename
        path.write_text(content, encoding="utf-8")
        return path
