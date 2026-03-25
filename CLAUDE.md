# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Idioma

Toda la comunicación, documentación y comentarios de código deben estar en **español**. Esto incluye respuestas en el chat, comentarios en el código, docstrings, archivos de documentación y mensajes de commit.

## Visión general

**AcademiaServer** es la infraestructura para **Mitzlia**, un asistente cognitivo académico para docentes. Captura ideas, procesa notas en lenguaje natural, gestiona recordatorios, genera documentos educativos (planeaciones, guiones, diapositivas) e integra con Telegram y Whisper (voz).

## Ejecutar el sistema

```bash
# Inicializar la base de datos (primera vez)
alembic upgrade head

# Servidor FastAPI
uvicorn academiaserver.api:app --reload

# Bot de Telegram (mensajes entrantes + agentes educativos)
python -m academiaserver.clients.telegram_bot

# Scheduler de recordatorios (proceso independiente)
python run_scheduler.py
```

## Migraciones (Alembic)

```bash
alembic upgrade head                                        # Aplicar migraciones pendientes
alembic revision --autogenerate -m "descripcion del cambio" # Nueva migración tras cambiar models.py
alembic downgrade -1                                        # Revertir última migración
```

Migraciones existentes: `0001_crear_tabla_notas.py`, `0002_agregar_entidades.py`.

## CLI (main.py)

```bash
python main.py save --content "..." [--title "..."]
python main.py get --id <id>
python main.py list
python main.py search <query> [--backend keyword|semantic]
python main.py log
python main.py digest
```

## Tests

```bash
pytest                                          # Todos los tests
pytest tests/test_api.py                        # Archivo específico
pytest tests/test_api.py::ApiTests::test_save_crea_nota_con_esquema_compatible  # Test específico
```

**Patrones de test:**
- Los tests usan `unittest.TestCase`. Para tests async usar `@pytest.mark.anyio` (`anyio` instalado; `pytest-asyncio` no está en el proyecto).
- Tests de FastAPI/BD: usar `StaticPool` de SQLAlchemy con SQLite in-memory. Hacer monkey-patch sobre `db_module.SessionLocal` y `db_module.engine` (no importar `SessionLocal` directamente).

## Arquitectura

Pipeline de procesamiento de mensajes:

```
Usuario (Telegram / CLI / FastAPI)
  → AgentRouter (detecta tareas educativas: planeacion, guion, slides)
      → EducationalAgent (system_prompt especializado → genera .md/.tex vía DocumentWriter)
  → AIOrchestrator (classify + enrich + parse reminders)
      → AIProvider (OllamaProvider | CloudProvider | ClaudeProvider | HybridProvider)
      → validate_ai_analysis → canonicalize_note → enrich_note_metadata
  → save_idea → SQLite via repository + EventBus
  → EmbeddingProvider (nomic-embed-text) → update_embedding

Scheduler (proceso independiente, intervalo configurable)
  → BD query → find due reminders → HTTP POST Telegram → mark reminded
```

### Módulos principales

- **`academiaserver/core.py`** — Lógica de negocio: `save_idea`, `search_ideas`, `get_memory_context`, `find_related_notes`, `reembed_notas`. Instancia un `EmbeddingProvider` singleton a nivel módulo.
- **`academiaserver/api.py`** — FastAPI: `POST /save`, `GET /list`, `GET /idea/{id}`, `GET /search?query&backend`, `GET /digest/daily`, `GET /log`.
- **`academiaserver/config.py`** — Toda la configuración desde `.env` con defaults. Fuente de verdad para variables de entorno.
- **`academiaserver/db/`** — `database.py` (engine, SessionLocal, Base, init_db), `models.py` (ORM `Nota`), `repository.py` (`save_nota`, `get_all_with_embeddings`, `update_embedding`, `_nota_to_dict`).
- **`academiaserver/events/bus.py`** — EventBus pub/sub singleton `bus`. Eventos: `nota.guardada`, `recordatorio.enviado`, `nota.enriquecida`.
- **`academiaserver/ai/`** — Capa IA:
  - `provider.py` — ABC `AIProvider` con método `analyze_message(text, context, memory, system_prompt_override)`.
  - `ollama_provider.py`, `cloud_provider.py` (OpenAI), `claude_provider.py` (Anthropic), `hybrid_provider.py`.
  - `orchestrator.py` — `AIOrchestrator`: reintentos, fallback a reglas, construcción de nota desde análisis IA.
  - `agent_router.py` — `AgentRouter`: detección regex de tareas docentes + enrutamiento a `EducationalAgent`.
  - `agents/` — `base.py` (ABC `EducationalAgent`), `planning.py`, `script.py`, `slides.py`. Los agentes inyectan su propio system prompt y soportan multi-turno vía `missing_info`.
  - `embedding_provider.py` — `EmbeddingProvider` (POST `/api/embed` Ollama, serialización float32 con `struct`).
  - `whisper_transcriber.py` — `WhisperTranscriber` (faster-whisper local → OpenAI fallback). Singleton `_whisper` en el bot.
  - `contract.py` — `validate_ai_analysis` valida el esquema JSON de salida de la IA.
  - `prompts.py` — System prompts para el orchestrator general.
- **`academiaserver/processing/`** — `pipeline.py` (fallback basado en reglas), `classifier.py`, `enrichment.py`, `reminders.py` (parseo de fechas/horas).
- **`academiaserver/search/`** — `keyword.py` (`KeywordSearchEngine`), `semantic.py` (`SemanticSearchEngine`, similitud coseno puro Python), `service.py` (`SearchService` solo maneja keyword).
- **`academiaserver/document_gen/`** — `writer.py` (`DocumentWriter`: guarda `.md`/`.tex` en `OUTPUTS_DIR` con nombre `YYYYMMDD_HHMMSS_<task>_<slug>`), `beamer.py` (`MarkdownToBeamer`: convierte Markdown a LaTeX Beamer).
- **`academiaserver/clients/telegram_bot.py`** — Bot Telegram: estado por chat (`_chat_contexts` deque maxlen=5, `_active_educational_tasks` para multi-turno educativo), routing educativo antes del orchestrator general.
- **`academiaserver/scheduler/reminders_scheduler.py`** — Proceso independiente: envía Telegram via HTTP directo (`requests`).

### Almacenamiento de datos

SQLite (`academia.db`) via SQLAlchemy ORM. Tabla `notas`. Schema gestionado por Alembic.

- `repository._nota_to_dict()` reconstruye el dict canónico con `metadata.enrichment.{topics,entities,summary,priority}`, `metadata.datetime`, `metadata.reminded`.
- Idempotencia: `repository.save_nota()` detecta duplicados via SHA-256 del contenido (`content_hash`, indexado).
- Embeddings: serializados como bytes `float32` con `struct`. `get_all_with_embeddings()` retorna solo notas con embedding. Para regenerar embeddings faltantes: `core.reembed_notas()`.

### Configuración de IA

Variable `AI_PROVIDER` en `.env`:
- `rules` (default) — Sin IA, solo clasificación por reglas.
- `ollama` — Solo local (modelo `qwen3:8b` por defecto).
- `cloud` — Proveedor cloud según `AI_CLOUD_PROVIDER` (`openai` o `claude`).
- `hybrid` — Ollama primero, fallback a cloud si falla (requiere `AI_ENABLE_CLOUD_FALLBACK=true`).

`AI_CLOUD_ALLOW_SENSITIVE=false` evita enviar mensajes sensibles a proveedores cloud.

### Agentes educativos (Fase 4.2)

`AgentRouter` detecta tareas en el texto via regex (`planeacion`, `guion`, `slides`) y enruta a `EducationalAgent`. Los agentes soportan multi-turno: si `missing_info != []`, el bot guarda el `task_type` en `_active_educational_tasks[chat_id]` y pregunta por los datos faltantes. Al completar, guarda la nota y envía el documento como adjunto en Telegram (`.md` para planeación/guión, `.tex` Beamer para diapositivas).

## Configuración (`.env`)

```
DB_PATH=academia.db
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
AI_PROVIDER=rules              # rules | ollama | cloud | hybrid
AI_CLOUD_PROVIDER=openai       # openai | claude
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBED_MODEL=nomic-embed-text
AI_ENABLE_CLOUD_FALLBACK=false
AI_CLOUD_ALLOW_SENSITIVE=false
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=1024
WHISPER_MODEL=small
WHISPER_LANGUAGE=es
WHISPER_DEVICE=cpu             # cuda en rubenpc
WHISPER_COMPUTE_TYPE=int8      # float16 en rubenpc con CUDA
SCHEDULER_INTERVAL_SECONDS=60
LOG_DIR=logs
OUTPUTS_DIR=outputs
TEMPLATES_DIR=templates
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```
