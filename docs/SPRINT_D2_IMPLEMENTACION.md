# Sprint D2 - Robustez y Fallback IA

Fecha: 6 de marzo de 2026

## Implementado

1. Validacion estricta de contrato IA
- Archivo: `academiaserver/ai/contract.py`
- Se valida:
  - `note_type` permitido
  - `title` obligatorio y acotado
  - `tags` como lista normalizada
  - `priority` permitida
  - `datetime` ISO o `null`
  - `reply_text` obligatorio y <= 220

2. Reintentos HTTP del cliente Ollama
- Archivo: `academiaserver/ai/ollama_provider.py`
- Reintentos ante errores de red/timeout con delay configurable.

3. Integracion del validador en orquestador
- Archivo: `academiaserver/ai/orchestrator.py`
- Si salida IA es invalida: fallback automatico a reglas.

4. Configuracion D2
- Archivo: `academiaserver/config.py`
- Nuevas variables:
  - `AI_HTTP_MAX_RETRIES`
  - `AI_HTTP_RETRY_DELAY_SECONDS`

## Pruebas

- `tests/test_ai_orchestrator.py`
  - incluye caso de payload invalido y fallback.
- `tests/test_ollama_provider.py`
  - incluye reintento exitoso y agotamiento de reintentos.

Resultado de suite:
- `16 tests OK`.
