# Sprint D - Implementacion IA Local con Ollama para Mitzlia

Fecha: 6 de marzo de 2026

## 1. Objetivo

Implementar una primera capa de IA local (Ollama) para procesar mensajes de Telegram y lograr, de forma simple y confiable:

1. Generar titulo de nota.
2. Clasificar tipo (`nota`, `recordatorio`, `idea`, `tarea`, `pregunta`).
3. Extraer metadatos utiles (fecha/hora, tags, prioridad).
4. Generar una respuesta breve y contextual al usuario.

Adicionalmente, dejar preparada una ruta hibrida con nube para mejoras de calidad cuando sea necesario.

---

## 2. Estado actual y punto de partida

El proyecto ya tiene:
- Bot de Telegram funcional.
- Pipeline base.
- Scheduler de recordatorios.
- Estructura de enriquecimiento y busqueda.

Este sprint no parte de cero; extiende lo ya construido con un modulo IA dedicado.

---

## 3. Alcance funcional (MVP de IA)

Para cada mensaje entrante de Telegram:

1. Mitzlia detecta intencion principal.
2. Construye una nota estructurada con esquema canonico.
3. Si es recordatorio, extrae datetime.
4. Guarda en inbox.
5. Responde al usuario con mensaje corto y natural.

Ejemplos de respuesta simple:
- `nota`: "Nota guardada. Tema principal: docencia."
- `idea`: "Idea registrada. ¿Quieres que la marque como proyecto potencial?"
- `recordatorio`: "Recordatorio guardado para hoy a las 18:00."
- `pregunta`: "Te puedo ayudar a buscar notas relacionadas. Escribe: /buscar <tema>."

---

## 4. Arquitectura propuesta

## 4.1 Nuevos modulos

- `academiaserver/ai/provider.py`
  - interfaz de proveedor LLM.
- `academiaserver/ai/ollama_provider.py`
  - cliente local Ollama para `chat` y `embed`.
- `academiaserver/ai/cloud_provider.py`
  - proveedor opcional nube (embeddings/LLM).
- `academiaserver/ai/orchestrator.py`
  - orquesta analisis del mensaje y salida estructurada.
- `academiaserver/ai/prompts.py`
  - prompts base en español.

## 4.2 Integracion con flujo existente

- Telegram -> `ai_orchestrator.process_message()` -> pipeline/core/scheduler.
- Si falla IA:
  - fallback a reglas actuales (clasificador existente) para no perder mensajes.

---

## 5. Diseño de salida estructurada

Formato objetivo por mensaje:

```json
{
  "note_type": "nota|recordatorio|idea|tarea|pregunta",
  "title": "titulo corto",
  "summary": "resumen breve",
  "tags": ["..."],
  "priority": "baja|media|alta",
  "datetime": "ISO-8601 o null",
  "reply_text": "respuesta breve para Telegram"
}
```

Reglas:
- `reply_text` maximo 220 caracteres.
- Si no hay certeza de `datetime`, usar `null` y preguntar aclaracion al usuario.
- Todo en español.

---

## 6. Plan por fases

## Fase D1 - Base local con Ollama (2-3 dias)

Entregables:
1. Configuracion IA en `.env`:
   - `AI_PROVIDER=ollama`
   - `OLLAMA_BASE_URL=http://localhost:11434`
   - `OLLAMA_CHAT_MODEL=gemma3`
   - `OLLAMA_EMBED_MODEL=embeddinggemma` (o `nomic-embed-text`)
2. Cliente Ollama para:
   - `POST /api/chat`
   - `POST /api/embed`
3. Prompt de clasificacion y titulacion en español.
4. Integracion minima con bot de Telegram.

Criterio de salida:
- 20 mensajes de prueba procesados sin perder persistencia.

## Fase D2 - Robustez y fallback (2 dias)

Entregables:
1. Validacion de JSON de salida IA.
2. Timeouts y reintentos del cliente Ollama.
3. Fallback a clasificador por reglas si falla IA.
4. Logs estructurados de:
   - `ai_inference_ok`
   - `ai_inference_error`
   - `ai_fallback_rules`

Criterio de salida:
- El bot nunca deja de guardar notas aunque Ollama falle.

## Fase D3 - Respuesta contextual simple (2 dias)

Entregables:
1. Plantillas de respuesta por tipo.
2. Respuesta con datos concretos (ID de nota, fecha de recordatorio).
3. Mensaje de aclaracion cuando falte fecha/hora.

Criterio de salida:
- Respuestas breves, utiles y consistentes en español.

## Fase D4 - Opcion hibrida nube (opcional, 2 dias)

Entregables:
1. `AI_PROVIDER=hybrid`.
2. Prioridad local; fallback nube solo si local falla.
3. Flags por tipo de dato sensible (ej. no enviar contenido privado).

Criterio de salida:
- Conmutacion sin interrumpir servicio.

---

## 7. Pruebas requeridas

## Unitarias
- parseo de salida IA a esquema esperado.
- manejo de salida incompleta o invalida.
- fallback de IA a reglas.

## Integracion
- mensaje Telegram -> nota guardada -> respuesta enviada.
- recordatorio con fecha -> scheduler lo ejecuta.
- recordatorio sin fecha -> se solicita aclaracion.

## Pruebas de calidad inicial
- set de 50 mensajes reales/anónimos.
- objetivo MVP:
  - clasificacion correcta >= 80%
  - titulo util >= 85%
  - respuesta aceptable >= 85%

---

## 8. Recomendacion de modelos para iniciar

## Local (Ollama)
- Chat:
  - `gemma3` (rapido para tareas de clasificacion/normalizacion)
- Embeddings:
  - `embeddinggemma` o `nomic-embed-text`

## Nube (opcional)
- Embeddings:
  - `text-embedding-3-small` para costo/latencia balanceado

---

## 9. Configuracion sugerida

```env
AI_PROVIDER=ollama
AI_TIMEOUT_SECONDS=25
AI_MAX_RETRIES=2

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma3
OLLAMA_EMBED_MODEL=embeddinggemma

AI_ENABLE_CLOUD_FALLBACK=false
OPENAI_API_KEY=
OPENAI_EMBED_MODEL=text-embedding-3-small
```

---

## 10. Riesgos y mitigaciones

- Riesgo: salida no estructurada del LLM.
  - Mitigacion: validacion estricta + fallback por reglas.

- Riesgo: latencia alta local.
  - Mitigacion: respuestas cortas, prompts compactos, timeout y retries bajos.

- Riesgo: clasificacion inestable.
  - Mitigacion: conjunto de ejemplos en prompt + evaluacion semanal.

---

## 11. Definicion de terminado del Sprint D (MVP)

Se considera completado cuando:

1. Mitzlia procesa mensajes de Telegram con IA local.
2. Genera titulo + tipo + respuesta breve en español.
3. Recordatorios siguen funcionando con scheduler.
4. Fallos de IA no bloquean guardado.
5. Existe reporte de precision inicial y backlog de mejoras.

---

## 12. Siguiente paso inmediato

Implementar Fase D1 en codigo:
1. crear `academiaserver/ai/ollama_provider.py`
2. crear `academiaserver/ai/orchestrator.py`
3. conectar el bot para usar orquestador
4. agregar pruebas de contrato de salida
