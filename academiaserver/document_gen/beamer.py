"""MarkdownToBeamer — convierte el outline Markdown del SlidesAgent a LaTeX Beamer UTEQ."""
import re
from pathlib import Path

from academiaserver.config import TEMPLATES_DIR

# ---------------------------------------------------------------------------
# Preamble UTEQ (Madrid theme + colores institucionales)
# ---------------------------------------------------------------------------
_PREAMBLE_TEMPLATE = r"""\documentclass[aspectratio=169]{beamer}

%% --- Tema y colores UTEQ ---
\usetheme{Madrid}
\definecolor{uteqAzul}{RGB}{0,48,135}
\definecolor{uteqNaranja}{RGB}{245,166,35}
\setbeamercolor{structure}{fg=uteqAzul}
\setbeamercolor{palette primary}{bg=uteqAzul,fg=white}
\setbeamercolor{palette secondary}{bg=uteqNaranja,fg=white}
\setbeamercolor{frametitle}{bg=uteqAzul,fg=white}
\setbeamercolor{title}{fg=uteqAzul}

%% --- Paquetes ---
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{amsmath}
\usepackage{hyperref}

%% --- Metadata ---
\title{%(title)s}
\author{%(author)s}
\institute{UTEQ}
\date{\today}

\begin{document}

\begin{frame}
  \titlepage
\end{frame}

"""

_FOOTER = r"""
\end{document}
"""


def _escape_latex(text: str) -> str:
    """Escapa caracteres especiales de LaTeX en el texto.

    Orden de escape importante (evitar doble-escape):
    ``&``, ``%``, ``$``, ``#``, ``^``, ``~``, ``{``, ``}``

    NO se escapa ``\\`` porque el texto generado por IA nunca contiene
    backslash literal; si lo tuviera, la compilación fallaría pero el
    archivo se enviaría igualmente (degradación aceptable).
    """
    replacements = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("^", r"\^{}"),
        ("~", r"\textasciitilde{}"),
    ]
    for char, escaped in replacements:
        text = text.replace(char, escaped)
    return text


def _apply_bold(text: str) -> str:
    """Convierte ``**texto**`` a ``\\textbf{texto}`` (aplicar DESPUÉS de _escape_latex)."""
    return re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)


def _process_inline(text: str) -> str:
    """Aplica escape LaTeX y conversión de bold al texto de una línea."""
    return _apply_bold(_escape_latex(text))


class MarkdownToBeamer:
    """Convierte el outline Markdown del SlidesAgent a un archivo .tex Beamer compilable.

    Parser de máquina de estados simple (línea a línea):

    * ``## Slide N — Título``  →  ``\\begin{frame}{Título}``
    * ``### Subsección``       →  ``\\medskip\\textbf{Subsección}``
    * ``- item``               →  ``\\item item`` (dentro de itemize)
    * Ignora: ``# H1``, ``| tablas |``, ``---``, líneas vacías fuera de frames

    Carga el preamble LaTeX desde ``templates/beamer/preamble.tex`` si existe;
    si no, usa el preamble hardcodeado ``_PREAMBLE_TEMPLATE`` como respaldo.
    Esto permite al Profesor personalizar la plantilla UTEQ sin tocar código.
    """

    def __init__(self, templates_dir: str | None = None):
        self._templates_dir = Path(templates_dir or TEMPLATES_DIR)

    def _load_preamble(self) -> str:
        """Lee ``templates/beamer/preamble.tex`` si existe; usa el hardcodeado como fallback."""
        preamble_path = self._templates_dir / "beamer" / "preamble.tex"
        if preamble_path.exists():
            return preamble_path.read_text(encoding="utf-8")
        return _PREAMBLE_TEMPLATE

    def convert(
        self, markdown_outline: str, title: str, author: str = "Profesor"
    ) -> str:
        """Retorna el contenido .tex completo como string.

        Args:
            markdown_outline: Texto Markdown generado por SlidesAgent.
            title: Título de la presentación (para preamble).
            author: Nombre del autor (para preamble).
        """
        preamble = self._load_preamble() % {
            "title": _escape_latex(title),
            "author": _escape_latex(author),
        }

        lines = markdown_outline.splitlines()
        body_parts: list[str] = []
        in_frame = False
        in_itemize = False

        def _close_itemize() -> None:
            nonlocal in_itemize
            if in_itemize:
                body_parts.append("  \\end{itemize}\n")
                in_itemize = False

        def _close_frame() -> None:
            nonlocal in_frame
            if in_frame:
                _close_itemize()
                body_parts.append("\\end{frame}\n\n")
                in_frame = False

        for raw_line in lines:
            line = raw_line.strip()

            # --- Encabezado H2: nuevo frame ---
            if line.startswith("## "):
                _close_frame()
                heading = line[3:].strip()
                # Eliminar prefijo "Slide N —" o "Slide N -" si existe
                heading = re.sub(
                    r"^Slide\s+\d+\s*[—–-]\s*", "", heading, flags=re.IGNORECASE
                ).strip()
                if not heading:
                    continue
                frame_title = _process_inline(heading)
                body_parts.append(f"\\begin{{frame}}{{\\frametitle{{{frame_title}}}}}\n")
                in_frame = True
                continue

            # --- Encabezado H3: subsección dentro del frame ---
            if line.startswith("### "):
                if not in_frame:
                    continue
                _close_itemize()
                subsec = _process_inline(line[4:].strip())
                body_parts.append(f"  \\medskip\\textbf{{{subsec}}}\n")
                continue

            # --- Ítem de lista ---
            if line.startswith("- ") or line.startswith("* "):
                if not in_frame:
                    continue
                if not in_itemize:
                    body_parts.append("  \\begin{itemize}\n")
                    in_itemize = True
                item_text = _process_inline(line[2:].strip())
                body_parts.append(f"    \\item {item_text}\n")
                continue

            # --- Ignorar: H1, tablas, separadores, líneas vacías ---
            # (No se agregan al body; simplemente se descartan)

        # Cerrar frame pendiente al final
        _close_frame()

        return preamble + "".join(body_parts) + _FOOTER
