# Sprint D3 - Respuesta Contextual y Aclaraciones

Fecha: 6 de marzo de 2026

## Objetivo

Mejorar la respuesta de Mitzlia por tipo de mensaje y asegurar aclaraciones cuando un recordatorio no tenga fecha/hora.

## Implementado

1. Motor de respuestas contextuales
- Archivo: `academiaserver/ai/replies.py`
- Plantillas por tipo:
  - `nota`
  - `recordatorio`
  - `idea`
  - `tarea`
  - `pregunta`

2. Flujo de aclaracion de recordatorios incompletos
- Archivo: `academiaserver/ai/orchestrator.py`
- Si `recordatorio` no tiene `datetime` (ni por IA ni por parser):
  - `metadata.needs_clarification = true`
  - `metadata.clarification_prompt` con instruccion en espanol
  - respuesta forzada de aclaracion al usuario

3. Politica de respuesta final
- Prioridad:
  1) aclaracion obligatoria (si aplica)
  2) `reply_text` de IA (si viene valido)
  3) plantilla contextual local

4. Ajuste de contrato IA
- Archivo: `academiaserver/ai/contract.py`
- `reply_text` puede venir vacio; en ese caso se usa plantilla contextual.
- Se mantienen validaciones estrictas del resto de campos.

## Pruebas

- `tests/test_ai_orchestrator.py`
  - `test_recordatorio_sin_datetime_pide_aclaracion`
  - `test_respuesta_contextual_cuando_ia_no_da_reply`

Resultado de suite:
- `18 tests OK`.

## Validacion manual sugerida (Telegram)

1. Enviar: `Recuérdame revisar el artículo`
   - Esperado: respuesta pidiendo fecha/hora.

2. Enviar: `Idea para organizar SEM por proyectos`
   - Esperado: respuesta contextual tipo idea.

3. Enviar: `Recuérdame mañana a las 18:30 revisar el artículo`
   - Esperado: respuesta con confirmacion de recordatorio con fecha/hora.
