# AcademiaServer

Infraestructura para **Mitzlia**, asistente cognitiva académica personal.

---

## Mitzlia

**Mitzlia** toma su nombre de *miztli*, el gato en la tradición náhuatl — símbolo de observación silenciosa, agilidad mental y presencia estratégica.

Al igual que el gato, Mitzlia observa sin interrumpir, recuerda sin olvidar, y actúa cuando el momento lo requiere.

Su propósito es funcionar como un **segundo cerebro digital** para el trabajo académico:

- capturar ideas en el momento en que aparecen
- organizar conocimiento sin fricción
- recordar compromisos antes de que se pierdan
- conectar lo que se sabe con lo que se está pensando
- amplificar el trabajo intelectual, no reemplazarlo

Mitzlia no pretende ser un asistente genérico.
Es una herramienta construida para un contexto específico: investigación, docencia y producción académica.

---

## Estado actual — v0.1

La v0.1 establece la infraestructura completa y las primeras capacidades de inteligencia asistida.

### Qué puede hacer hoy

- Recibir notas, ideas, tareas y recordatorios por Telegram
- Clasificar y enriquecer cada nota con IA local (qwen3:8b)
- Extraer entidades, temas y resumen semántico de cada nota
- Recordar al Profesor compromisos pendientes en el momento exacto
- Buscar notas por similitud semántica (no solo palabras clave)
- Consultar su historial antes de responder — memoria activa (RAG)
- Mantener contexto conversacional dentro de la misma sesión
- Responder con voz propia, directa y sin relleno genérico
- Exponer toda su funcionalidad vía API REST y CLI

### Qué sabe Mitzlia sobre su usuario

- Que es Profesor e investigador
- Que trabaja con SEM, hipótesis, artículos y clases
- Que el tiempo es limitado — las respuestas deben ser breves
- Que la honestidad sobre los datos importa más que sonar segura

---

## Ecosistema de dispositivos

Mitzlia está diseñada para acompañar al Profesor en tres contextos distintos con una sola memoria compartida:

| Dispositivo | Ubicación | Uso principal con Mitzlia |
|---|---|---|
| `rubenpc` (GPU) | Casa — laboratorio personal | Servidor central. Corre Ollama, AcademiaServer y el scheduler 24/7. Trabajo profundo de investigación. |
| Mini-PC oficina | Universidad — oficina | Preparar clases, seguimiento de proyectos, reuniones. Accede a `rubenpc` vía Tailscale. |
| Laptop | Universidad — aula | Impartición de clases presenciales. Captura de ideas durante la clase. |
| iPhone 12 | En movimiento | Captura rápida de ideas, notas de voz, recordatorios entre reuniones. Usa Telegram desde cualquier red. |

**Principio clave:** Ollama corre únicamente en `rubenpc` aprovechando la GPU. El resto de los dispositivos acceden a él a través de la red privada Tailscale — sin necesidad de instalar modelos localmente ni abrir puertos al internet público.

---

## Arquitectura

El sistema sigue una arquitectura modular orientada a eventos:

```
Profesor (Telegram / CLI / FastAPI)
  ↓
Pipeline (clasificar + enriquecer + parsear recordatorios)
  ↓
Memoria activa — RAG (busca notas relevantes antes de responder)
  ↓
AI Orchestrator
  ├── Ollama local  →  qwen3:8b   (chat)
  │                    nomic-embed-text  (embeddings)
  └── OpenAI cloud  →  fallback opcional
  ↓
Canonicalizar nota
  ↓
SQLite via SQLAlchemy  (academia.db)
  ↓
Bus de eventos pub/sub
  ↓
Logger  (logs/activity.log)

Scheduler (proceso independiente, loop cada 60s)
  ↓
Consulta BD → Recordatorios vencidos → HTTP POST Telegram → Marca enviados
```

### Stack técnico

| Capa | Tecnología |
|---|---|
| API REST | FastAPI + Uvicorn |
| Bot | python-telegram-bot |
| Base de datos | SQLite + SQLAlchemy + Alembic |
| IA (chat) | Ollama — qwen3:8b |
| IA (embeddings) | Ollama — nomic-embed-text (768 dims) |
| Búsqueda semántica | Cosine similarity en Python puro |
| Fallback cloud | OpenAI (opcional) |
| Configuración | python-dotenv |

### Módulos principales

```
academiaserver/
  api.py                  → FastAPI: /save, /list, /idea/{id}, /search, /digest/daily, /log
  core.py                 → Lógica central: save, list, search, reembed, get_memory_context
  config.py               → Toda la configuración desde .env
  db/
    database.py           → Engine SQLAlchemy, SessionLocal, Base
    models.py             → ORM Nota (tabla notas)
    repository.py         → Acceso a datos + funciones de embedding
  ai/
    embedding_provider.py → Genera vectores float32 via Ollama /api/embed
    orchestrator.py       → Orquesta IA: reintentos, fallback, construcción de nota
    prompts.py            → System prompt con personalidad de Mitzlia + fecha dinámica
    contract.py           → Validación y normalización del JSON de salida
    ollama_provider.py    → Provider local (qwen3:8b)
    cloud_provider.py     → Provider cloud (OpenAI)
    hybrid_provider.py    → Local primero, cloud como fallback
  search/
    semantic.py           → SemanticSearchEngine (cosine similarity)
    keyword.py            → KeywordSearchEngine
  processing/
    pipeline.py           → Clasificación y enriquecimiento por reglas
    enrichment.py         → Extrae topics/prioridad; no sobreescribe datos de IA
    reminders.py          → Parser de fechas relativas
  clients/
    telegram_bot.py       → Bot: maneja mensajes, memoria activa, contexto conversacional
  scheduler/
    reminders_scheduler.py → Proceso independiente de recordatorios
  events/
    bus.py                → Bus pub/sub (singleton)
  digest/                 → Generación de resumen diario
migrations/               → Alembic: 0001_crear_tabla_notas, 0002_agregar_entidades
```

---

## Puesta en marcha

### Requisitos

- Python 3.12+
- [Ollama](https://ollama.com) instalado y corriendo
- Token de bot de Telegram (`@BotFather`)
- (Opcional) API key de OpenAI para fallback cloud

### Modelos necesarios

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### Instalación

```bash
pip install -r requirements.txt
cp .env.example .env   # editar con tus valores
alembic upgrade head   # inicializar base de datos
```

### Ejecutar los procesos

Cada componente es un proceso independiente:

```bash
# API REST
uvicorn academiaserver.api:app --host 0.0.0.0 --port 8000 --reload

# Bot de Telegram
python -m academiaserver.clients.telegram_bot

# Scheduler de recordatorios
python run_scheduler.py
```

### CLI

```bash
python main.py save --content "..."          # guardar nota
python main.py list                          # listar notas
python main.py get --id 20260308-001         # obtener nota por ID
python main.py search "SEM" --backend semantic   # búsqueda semántica
python main.py search "clase" --backend keyword  # búsqueda por palabras
python main.py reembed                       # generar embeddings para notas sin vector
python main.py digest                        # resumen del día
```

### Migraciones de base de datos

```bash
alembic upgrade head              # aplicar todas las migraciones
alembic revision --autogenerate -m "descripcion"  # nueva migración tras cambiar models.py
alembic downgrade -1              # revertir última migración
```

### Tests

```bash
pytest                            # todos los tests
pytest tests/test_embeddings.py  # un archivo específico
pytest tests/ -v                 # con detalle
```

---

## Variables de configuración (.env)

```env
# Base de datos
DB_PATH=academia.db

# Telegram
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=

# IA — Ollama
AI_PROVIDER=ollama               # ollama | cloud | hybrid
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

# IA — OpenAI (fallback opcional)
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
AI_ENABLE_CLOUD_FALLBACK=false
AI_CLOUD_ALLOW_SENSITIVE=false

# Scheduler
SCHEDULER_INTERVAL_SECONDS=60

# Servidor
LOG_DIR=logs
```

---

## Filosofía de desarrollo

**Estabilidad antes que complejidad.**
Cada nueva capacidad se construye sobre una base que ya funciona.

**Infraestructura antes que automatización.**
No automatizar lo que no está bien estructurado.

**Automatización antes que autonomía.**
No dar autonomía a lo que no está bien automatizado.

**Honestidad sobre los datos.**
Mitzlia solo afirma lo que está en las notas. Nunca inventa.

---

## Roadmap

### v0.1 — Infraestructura + Inteligencia asistida ✅
- SQLite + Alembic, bus de eventos, scheduler desacoplado
- Embeddings vectoriales y búsqueda semántica
- Enriquecimiento real con qwen3:8b (entidades, topics, resumen)
- Contexto conversacional por sesión (últimos 5 mensajes)
- Memoria activa RAG (historial relevante antes de cada respuesta)
- Personalidad de Mitzlia: directa, honesta, conoce el contexto académico

### v0.2 — Despliegue permanente (Tailscale)
`rubenpc` se convierte en el servidor central de Mitzlia, accesible desde cualquier dispositivo del ecosistema a través de la red privada Tailscale — sin exponer puertos al internet público.

La red ya existe. Lo que falta es formalizar el despliegue:

- `.env.example` documentado para cada contexto (rubenpc, oficina, laptop)
- Scripts de arranque automático para los tres procesos en rubenpc (API, bot, scheduler)
- `OLLAMA_BASE_URL` configurado con la IP Tailscale de rubenpc en los equipos que no tienen GPU
- Acceso a la API REST desde mini-PC de oficina, laptop del aula y iPhone vía Tailscale
- Guía de configuración por dispositivo

Con esto, el Profesor escribe desde el aula, la oficina o el teléfono — Mitzlia siempre responde desde `rubenpc`.

### v0.3 — Voz
El Profesor puede enviar notas de voz desde Telegram. Mitzlia las transcribe con Whisper local en `rubenpc` y las procesa igual que texto.

Caso de uso central: capturar ideas durante una clase presencial sin interrumpir el flujo, o dictar una nota caminando entre edificios.

- Integración de Whisper (transcripción local en rubenpc, audio nunca sale a la nube)
- Pipeline: nota de voz → texto → clasificación → nota/recordatorio
- Compatible con todos los dispositivos: iPhone, laptop del aula, mini-PC
- Sin cambios en la interfaz: el Profesor habla, Mitzlia captura

### v0.4 — Memoria profunda
Mitzlia detecta y verbaliza conexiones entre notas capturadas en distintos momentos y contextos — lo que se pensó en el laboratorio, lo que surgió en clase, lo que se anotó en una reunión de oficina.

- Grafo de ideas: notas relacionadas entre sí por similitud semántica
- Mitzlia puede decir: "Esto conecta con lo que guardó sobre el Dr. García la semana pasada"
- Agrupamiento automático por proyecto o tema activo, independientemente del dispositivo de origen
- Vista de "hilos": secuencias de notas relacionadas en el tiempo
- Detección de proyectos sin actividad reciente: "Profesor, no ha registrado nada sobre el artículo SEM en dos semanas"

### v0.5 — Escritura asistida
Mitzlia ayuda a convertir notas en texto académico.

- Síntesis de múltiples notas en un borrador estructurado
- Generación de secciones de artículos o reportes a partir del historial
- Exportación a Markdown y LaTeX
- Sugerencias de estructura para artículos o presentaciones

### v0.6 — Agentes especializados
Mitzlia delega tareas a agentes con conocimiento específico.

- Agente de investigación: busca en fuentes académicas externas
- Agente de docencia: organiza material de cursos a partir de notas
- Agente de escritura: revisa y sugiere mejoras en borradores

### v1.0 — Laboratorio cognitivo
Mitzlia actúa de forma semi-autónoma sobre el conocimiento del Profesor.

- Propone conexiones y acciones sin que el Profesor pregunte
- Identifica proyectos sin avance y pregunta si siguen activos
- Multi-dispositivo coordinado: misma memoria desde cualquier equipo
- Posible integración con Obsidian, Zotero u otras herramientas académicas

---

## Principio fundamental

Mitzlia observa.
Mitzlia recuerda.
Mitzlia actúa cuando es necesario.
