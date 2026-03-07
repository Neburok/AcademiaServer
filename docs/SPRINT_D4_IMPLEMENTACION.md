# Sprint D4 - Modo Hibrido (Local + Nube)

Fecha: 6 de marzo de 2026

## Objetivo

Habilitar un proveedor IA hibrido:
- Local (Ollama) como ruta principal.
- Nube como fallback opcional.
- Regla de privacidad para no enviar mensajes sensibles a nube.

## Implementado

1. Proveedor cloud
- Archivo: `academiaserver/ai/cloud_provider.py`
- Integracion via `chat/completions` con salida JSON.

2. Proveedor hibrido
- Archivo: `academiaserver/ai/hybrid_provider.py`
- Flujo:
  - intenta local
  - si falla, evalua fallback cloud
  - bloquea cloud para mensajes sensibles cuando la politica lo indique

3. Deteccion de mensajes sensibles
- Archivo: `academiaserver/ai/privacy.py`
- Reglas por patrones (password, token, api key, etc.).

4. Integracion en bot
- Archivo: `academiaserver/clients/telegram_bot.py`
- Soporta `AI_PROVIDER=ollama|cloud|hybrid|rules`.

5. Configuracion
- Archivo: `academiaserver/config.py`
- Variables nuevas:
  - `AI_CLOUD_ALLOW_SENSITIVE`
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_CHAT_MODEL`

## Pruebas

- `tests/test_hybrid_provider.py`
  - usa local si funciona
  - usa cloud si local falla
  - bloquea cloud con mensaje sensible

Resultado de suite:
- `23 tests OK`.
