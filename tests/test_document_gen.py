"""Tests para academiaserver.document_gen (writer.py y beamer.py)."""
import tempfile
import unittest
from pathlib import Path

from academiaserver.document_gen.writer import DocumentWriter, _slugify
from academiaserver.document_gen.beamer import MarkdownToBeamer, _escape_latex


# ===========================================================================
# Tests de _slugify
# ===========================================================================


class SlugifyTests(unittest.TestCase):
    def test_texto_simple(self):
        self.assertEqual(_slugify("hola mundo"), "hola_mundo")

    def test_tildes_eliminadas(self):
        self.assertEqual(_slugify("Física y Química"), "fisica_y_quimica")

    def test_eñe_eliminada(self):
        self.assertEqual(_slugify("planeación"), "planeacion")

    def test_caracteres_especiales(self):
        self.assertEqual(_slugify("Clase #1: Intro!"), "clase_1_intro")

    def test_espacios_multiples(self):
        self.assertEqual(_slugify("  dos  espacios  "), "dos_espacios")

    def test_truncado(self):
        largo = "a" * 50
        resultado = _slugify(largo, max_chars=10)
        self.assertEqual(len(resultado), 10)

    def test_cadena_vacia(self):
        self.assertEqual(_slugify(""), "")

    def test_solo_numeros(self):
        self.assertEqual(_slugify("123"), "123")

    def test_mayusculas_a_minusculas(self):
        self.assertEqual(_slugify("UTEQ Física I"), "uteq_fisica_i")


# ===========================================================================
# Tests de DocumentWriter
# ===========================================================================


class DocumentWriterTests(unittest.TestCase):
    def setUp(self):
        """Crea un directorio temporal para cada test."""
        self._tmpdir = tempfile.TemporaryDirectory()
        self.writer = DocumentWriter(outputs_dir=self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    # --- save_markdown ---

    def test_save_markdown_crea_archivo(self):
        path = self.writer.save_markdown("# Hola", "planeacion", "Mi Planeación")
        self.assertTrue(path.exists())

    def test_save_markdown_extension_correcta(self):
        path = self.writer.save_markdown("contenido", "planeacion", "Titulo")
        self.assertEqual(path.suffix, ".md")

    def test_save_markdown_contenido_fiel(self):
        contenido = "# Encabezado\n- item uno\n- item dos"
        path = self.writer.save_markdown(contenido, "guion", "Test")
        self.assertEqual(path.read_text(encoding="utf-8"), contenido)

    def test_save_markdown_nombre_tiene_timestamp(self):
        path = self.writer.save_markdown("x", "planeacion", "Test")
        # El nombre debe tener formato YYYYMMDD_HHMMSS_...
        import re
        self.assertRegex(path.name, r"^\d{8}_\d{6}_")

    def test_save_markdown_nombre_tiene_slug(self):
        path = self.writer.save_markdown("x", "planeacion", "Ley de Ohm")
        self.assertIn("ley_de_ohm", path.name)

    def test_save_markdown_nombre_tiene_task_type(self):
        path = self.writer.save_markdown("x", "guion", "Test")
        self.assertIn("guion", path.name)

    def test_save_markdown_crea_directorio_si_no_existe(self):
        subdir = Path(self._tmpdir.name) / "subdir" / "anidado"
        writer = DocumentWriter(outputs_dir=str(subdir))
        path = writer.save_markdown("x", "slides", "Test")
        self.assertTrue(path.exists())

    # --- save_tex ---

    def test_save_tex_extension_correcta(self):
        path = self.writer.save_tex("\\documentclass{beamer}", "slides", "Presentacion")
        self.assertEqual(path.suffix, ".tex")

    def test_save_tex_contenido_fiel(self):
        contenido = "\\documentclass{beamer}\n\\begin{document}\n\\end{document}"
        path = self.writer.save_tex(contenido, "slides", "Test")
        self.assertEqual(path.read_text(encoding="utf-8"), contenido)

    def test_save_tex_nombre_tiene_slug(self):
        path = self.writer.save_tex("x", "slides", "Transferencia de Calor")
        self.assertIn("transferencia_de_calor", path.name)


# ===========================================================================
# Tests de MarkdownToBeamer
# ===========================================================================

_OUTLINE_COMPLETO = """
# Outline de Presentación — Ley de Ohm

| Campo | Valor |
|-------|-------|
| Tema | Ley de Ohm |

---

## Slide 1 — Portada
- **Título:** Ley de Ohm
- **Autor:** Profesor García

## Slide 2 — Agenda
- Introducción al circuito eléctrico
- Definición de resistencia

## Slide 3 — Conceptos Básicos
### Definiciones:
- Voltaje (V)
- Corriente (I)
- Resistencia (R)
### Fórmula:
- V = I × R

## Slide 4 — Resumen
- V = I × R
- Aplicaciones prácticas
"""


class MarkdownToBeamerTests(unittest.TestCase):
    def setUp(self):
        self.converter = MarkdownToBeamer()
        self.tex = self.converter.convert(_OUTLINE_COMPLETO, title="Ley de Ohm")

    def test_genera_begin_document(self):
        self.assertIn(r"\begin{document}", self.tex)

    def test_genera_end_document(self):
        self.assertIn(r"\end{document}", self.tex)

    def test_genera_frames(self):
        self.assertIn(r"\begin{frame}", self.tex)

    def test_genera_end_frame(self):
        self.assertIn(r"\end{frame}", self.tex)

    def test_titulo_en_preamble(self):
        self.assertIn(r"\title{Ley de Ohm}", self.tex)

    def test_autor_en_preamble(self):
        self.assertIn(r"\author{Profesor}", self.tex)

    def test_institute_uteq(self):
        self.assertIn(r"\institute{UTEQ}", self.tex)

    def test_paquete_inputenc(self):
        self.assertIn(r"\usepackage[utf8]{inputenc}", self.tex)

    def test_paquete_babel_spanish(self):
        self.assertIn(r"\usepackage[spanish]{babel}", self.tex)

    def test_tema_madrid(self):
        self.assertIn(r"\usetheme{Madrid}", self.tex)

    def test_color_azul_uteq(self):
        self.assertIn("uteqAzul", self.tex)
        self.assertIn("RGB}{0,48,135}", self.tex)

    def test_color_naranja_uteq(self):
        self.assertIn("uteqNaranja", self.tex)
        self.assertIn("RGB}{245,166,35}", self.tex)

    def test_items_generados(self):
        self.assertIn(r"\item", self.tex)

    def test_itemize_abierto_y_cerrado(self):
        self.assertIn(r"\begin{itemize}", self.tex)
        self.assertIn(r"\end{itemize}", self.tex)

    def test_subseccion_como_textbf(self):
        self.assertIn(r"\medskip\textbf{Definiciones:}", self.tex)

    def test_bold_convertido_a_textbf(self):
        # **Título:** en el Markdown → \textbf{Título:}
        self.assertIn(r"\textbf{T", self.tex)

    def test_tablas_ignoradas(self):
        # Las líneas | tabla | no deben aparecer como \item
        self.assertNotIn("| Campo |", self.tex)

    def test_separadores_ignorados(self):
        # Los '---' de Markdown no deben generar frames ni items
        # (pueden aparecer en comentarios del preamble, pero no como contenido)
        self.assertNotIn(r"\item ---", self.tex)
        self.assertNotIn(r"\frametitle{---}", self.tex)

    def test_h1_ignorado(self):
        # El H1 "# Outline de Presentación" no debe generar frame
        self.assertNotIn("Outline de Presentaci", self.tex)

    def test_outline_vacio_no_crashea(self):
        tex = self.converter.convert("", title="Vacio")
        self.assertIn(r"\begin{document}", tex)
        self.assertIn(r"\end{document}", tex)

    def test_frame_sin_items_valido(self):
        outline = "## Slide 1 — Solo título\n"
        tex = self.converter.convert(outline, title="Test")
        self.assertIn(r"\begin{frame}", tex)
        self.assertNotIn(r"\begin{itemize}", tex)

    def test_autor_personalizado(self):
        tex = self.converter.convert("", title="X", author="Dr. Ruben")
        self.assertIn(r"\author{Dr. Ruben}", tex)


class MarkdownToBeamerTemplateExternoTests(unittest.TestCase):
    """Verifica el comportamiento de _load_preamble() con templates externos."""

    def test_usa_preamble_externo_si_existe(self):
        """Si templates/beamer/preamble.tex existe, lo usa en lugar del hardcodeado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            preamble_dir = Path(tmpdir) / "beamer"
            preamble_dir.mkdir(parents=True)
            custom_preamble = (
                r"\documentclass{beamer}" + "\n"
                r"\title{%(title)s}" + "\n"
                r"\author{%(author)s}" + "\n"
                r"\begin{document}" + "\n"
            )
            (preamble_dir / "preamble.tex").write_text(custom_preamble, encoding="utf-8")
            converter = MarkdownToBeamer(templates_dir=tmpdir)
            tex = converter.convert("## Slide 1 — Test\n- item", title="Test")
            # Debe usar el preamble personalizado (no tiene \usetheme{Madrid})
            self.assertIn(r"\documentclass{beamer}", tex)
            self.assertNotIn(r"\usetheme{Madrid}", tex)

    def test_fallback_preamble_si_no_existe_directorio(self):
        """Con templates_dir inexistente, usa el preamble hardcodeado."""
        converter = MarkdownToBeamer(templates_dir="/directorio/no/existe")
        tex = converter.convert("", title="Test")
        self.assertIn(r"\usetheme{Madrid}", tex)  # viene del hardcodeado

    def test_fallback_preamble_si_no_existe_archivo(self):
        """Con templates_dir vacío (sin preamble.tex), usa el preamble hardcodeado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = MarkdownToBeamer(templates_dir=tmpdir)
            tex = converter.convert("", title="Test")
            self.assertIn("uteqAzul", tex)  # viene del hardcodeado


class EscapeLatexTests(unittest.TestCase):
    def test_escapa_ampersand(self):
        self.assertEqual(_escape_latex("A & B"), r"A \& B")

    def test_escapa_porcentaje(self):
        self.assertEqual(_escape_latex("50%"), r"50\%")

    def test_escapa_dolar(self):
        self.assertEqual(_escape_latex("$100"), r"\$100")

    def test_escapa_numeral(self):
        self.assertEqual(_escape_latex("#1"), r"\#1")

    def test_texto_sin_especiales_sin_cambio(self):
        self.assertEqual(_escape_latex("hola mundo"), "hola mundo")


if __name__ == "__main__":
    unittest.main()
