# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Idioma

Toda la comunicación, documentación y comentarios de código deben estar en **español**. Esto incluye respuestas en el chat, comentarios en el código, docstrings, archivos de documentación y mensajes de commit.

## Project Overview

**AcademiaServer** is the backend infrastructure for **Mitzlia**, an intelligent academic cognitive assistant. It captures ideas, processes natural language notes, manages reminders, and integrates with Telegram. The system is designed as a personal "second brain" for academic work.

## Running the System

```bash
# Inicializar la base de datos (primera vez)
alembic upgrade head

# Iniciar el servidor FastAPI
uvicorn academiaserver.api:app --reload

# Iniciar el bot de Telegram (solo maneja mensajes entrantes)
python -m academiaserver.clients.telegram_bot

# Iniciar el scheduler de recordatorios (proceso independiente)
python run_scheduler.py
```

## Database Migrations (Alembic)

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Crear nueva migración tras cambiar models.py
alembic revision --autogenerate -m "descripcion del cambio"

# Revertir última migración
alembic downgrade -1
```

## CLI Commands (main.py)

```bash
python main.py save --content "..." [--title "..."]   # Guardar nota
python main.py get --id <note_id>                      # Obtener nota por ID
python main.py list                                    # Listar todas las notas
python main.py search <query> [--backend keyword]      # Buscar notas
python main.py log                                     # Mostrar logs de actividad
python main.py digest                                  # Generar digest diario
```

## Running Tests

```bash
pytest                          # Ejecutar todos los tests
pytest tests/test_file.py       # Ejecutar un archivo de tests
pytest tests/test_file.py::test_name  # Ejecutar un test específico
```

## Architecture

The system follows an event-driven modular pipeline:

```
User (Telegram / CLI / FastAPI)
  → Pipeline (classify + enrich + parse reminders)
  → AI Orchestrator (Ollama local → OpenAI cloud fallback)
  → Canonicalize Note
  → Save to SQLite (academiaserver/db/) via EventBus
  → Logger (logs/activity.log)

Scheduler (60s loop, proceso independiente)
  → DB query → Find due reminders → HTTP POST Telegram → Mark reminded
```

### Key Modules

- **`academiaserver/api.py`** — FastAPI REST endpoints (`/save`, `/list`, `/idea/{id}`, `/search`, `/digest/daily`, `/log`)
- **`academiaserver/core.py`** — Core business logic: save/load/search ideas (usa repository + bus de eventos)
- **`academiaserver/config.py`** — All configuration from `.env`, with defaults
- **`academiaserver/db/`** — Capa de datos SQLite+SQLAlchemy: `database.py`, `models.py`, `repository.py`
- **`academiaserver/events/bus.py`** — Bus de eventos pub/sub (singleton `bus`). Eventos: `nota.guardada`, `recordatorio.enviado`, `nota.enriquecida`
- **`academiaserver/processing/`** — Classification (nota vs. recordatorio), enrichment, reminder datetime parsing
- **`academiaserver/ai/`** — AI layer: `OllamaProvider`, `CloudProvider`, `HybridProvider` orchestrated by `AIOrchestrator`; includes privacy detection and output schema validation
- **`academiaserver/scheduler/reminders_scheduler.py`** — Proceso independiente: consulta la BD, envía Telegram via HTTP directo, marca como enviados
- **`academiaserver/clients/telegram_bot.py`** — Bot de Telegram (solo maneja mensajes entrantes, sin scheduler)
- **`academiaserver/search/`** — `KeywordSearchEngine` (implemented); `SemanticSearchEngine` (stub for future embeddings)
- **`academiaserver/digest/`** — Daily summary generation
- **`migrations/`** — Migraciones Alembic. Primera: `0001_crear_tabla_notas.py`

### Data Storage

Notes are stored in **SQLite** (`academia.db`) via SQLAlchemy ORM. Table: `notas`. Schema managed by Alembic.

- `repository._nota_to_dict()` reconstructs the canonical dict format (with nested `metadata`) for backward compatibility with all existing modules.
- Idempotency: duplicate content is detected via SHA-256 hash (`content_hash` field, indexed).

### AI Configuration

The AI layer supports three modes via `AI_PROVIDER` in `.env`:
- `ollama` — Local-only (Ollama, model `gemma3:4b` by default)
- `cloud` — OpenAI only
- `hybrid` — Tries Ollama first, falls back to OpenAI if it fails

`AI_CLOUD_ALLOW_SENSITIVE=false` prevents sensitive messages from being sent to cloud providers.

## Configuration (`.env`)

Key variables:
- `DB_PATH` — SQLite database path (default: `academia.db`)
- `TELEGRAM_TOKEN` / `TELEGRAM_CHAT_ID` — Bot credentials (used by both bot and scheduler)
- `AI_PROVIDER` — `ollama | cloud | hybrid`
- `OLLAMA_BASE_URL` / `OLLAMA_CHAT_MODEL`
- `OPENAI_API_KEY`
- `SCHEDULER_INTERVAL_SECONDS` — Reminder check frequency (default: 60)
- `LOG_DIR` — Log directory (default: `logs`)

## Development Roadmap

Infrastructure vulnerabilities corrected (Sprints A-E): SQLite storage, Alembic migrations, idempotency, event bus, decoupled scheduler. **Phase 3** (Assisted Intelligence) is next: semantic search via embeddings (sqlite-vec) and advanced AI enrichment.
