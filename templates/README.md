# Plantillas UTEQ para Mitzlia

Este directorio contiene las plantillas LaTeX que Mitzlia usa al generar documentos académicos.
Puedes editar o reemplazar estos archivos sin tocar código Python.

## Estructura

```
templates/
└── beamer/
    └── preamble.tex    ← Preamble LaTeX Beamer con identidad UTEQ
```

## Cómo personalizar

### Presentaciones Beamer (`templates/beamer/preamble.tex`)

Mitzlia lee este archivo al generar slides. Puedes modificarlo libremente:

- **Añadir el logo**: Descomenta las líneas `\usepackage{graphicx}` y `\logo{...}`,
  y coloca `logo_uteq.png` en esta misma carpeta (`templates/beamer/`).
- **Cambiar el tema**: Reemplaza `\usetheme{Madrid}` por otro tema Beamer.
- **Actualizar colores**: Modifica los valores RGB de `uteqAzul` y `uteqNaranja`.
- **Añadir paquetes**: Agrega `\usepackage{...}` según tus necesidades.

> **Importante:** Mantén los marcadores `%(title)s` y `%(author)s` en el preamble.
> Mitzlia los sustituye automáticamente con el título y autor de cada presentación.
> Si los eliminas, el `.tex` se genera sin título/autor pero sigue siendo válido.

### Fallback automático

Si el archivo `preamble.tex` no existe o `TEMPLATES_DIR` no está configurado,
Mitzlia usa un preamble UTEQ interno como respaldo. El sistema nunca falla
por falta de plantillas.

## Variables de entorno

```ini
# En tu .env (por defecto ya apunta aquí):
TEMPLATES_DIR=templates
```

## Plantillas futuras

| Tipo de documento | Directorio sugerido | Estado |
|---|---|---|
| Presentaciones Beamer | `templates/beamer/` | ✅ Implementado |
| Exámenes / prácticas LaTeX | `templates/latex/` | Pendiente |
| Reportes de práctica | `templates/reportes/` | Pendiente |
