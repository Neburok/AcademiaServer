# Plan de Desarrollo (6 de marzo de 2026)

Este plan conecta el estado real del proyecto con el roadmap y define los siguientes pasos de ejecucion.

---

## 1. Verificacion de Etapa Actual

Referencia del roadmap:
- Fase 1: Infraestructura fundacional
- Fase 2: Automatizacion
- Fase 3: Inteligencia asistida

Etapa real actual:
- El proyecto esta en **Fase 2 (Automatizacion), parcialmente completa**.
- Hay avance funcional en:
  - integracion con Telegram
  - pipeline de procesamiento
  - scheduler de recordatorios
  - comportamiento bidireccional basico (captura + notificacion)
- Antes de pasar a Fase 3 se requiere una compuerta de estabilidad en Fase 2.

---

## 2. Brechas Actuales (Bloquean Fase 3)

### Bloqueos criticos
- `processing/pipeline.py` podia lanzar `UnboundLocalError` en notas no recordatorio.
- Contrato inconsistente entre API y funcion central de guardado.
- Deteccion de recordatorios fragil ante variaciones de lenguaje.

### Brechas operativas
- `CHAT_ID` fijo en el cliente de Telegram.
- Sin politica basica de error/reintento para envio de recordatorios.
- Ciclo de vida del scheduler acoplado al loop del bot.

### Brechas de calidad
- Cobertura automatica insuficiente para pipeline/scheduler/API.
- Criterios de salida por fase no explicitados en pruebas.

---

## 3. Plan de Ejecucion

## Sprint A - Estabilizacion del Core de Automatizacion (Compuerta Fase 2)
Ventana objetivo: 6-13 marzo 2026

Objetivos:
- Hacer confiable el flujo captura -> proceso -> persistencia.
- Hacer idempotente y observable el envio de recordatorios.

Entregables:
- Corregir bug de flujo en pipeline.
- Unificar contrato API/core de guardado.
- Normalizar reglas de deteccion de recordatorios.
- Quitar `chat_id` hardcodeado y moverlo a configuracion.
- Agregar pruebas minimas para:
  - procesamiento de nota normal
  - procesamiento de recordatorio
  - deteccion de recordatorios vencidos
  - marcado de recordatorios enviados

Criterio de salida:
- Flujo end-to-end de guardado por Telegram funcional para nota y recordatorio.
- Scheduler no reenvia recordatorios ya procesados.
- Pruebas base en verde localmente.

## Sprint B - Endurecimiento Operativo
Ventana objetivo: 13-20 marzo 2026

Objetivos:
- Mejorar confiabilidad para operacion continua.

Entregables:
- Logs estructurados para pipeline y scheduler.
- Politica basica de reintentos para fallos de envio por Telegram.
- Validaciones de arranque (token, chat id, rutas).
- Runbook de despliegue local y mini-PC.

Criterio de salida:
- Fallos recuperables se registran y reintentan.
- Reinicios no provocan duplicados de recordatorios.

## Sprint C - Fundaciones para Fase 3 (IA Readiness)
Ventana objetivo: 20-27 marzo 2026

Objetivos:
- Preparar modelo de datos y flujo para capacidades de inteligencia asistida.

Entregables:
- Definicion canonica y versionada del esquema de nota.
- Ganchos de enriquecimiento de metadatos.
- Capa de busqueda abstraida (keyword ahora, semantica despues).
- Prototipo de digest diario.

Criterio de salida:
- El sistema puede generar un resumen diario a partir de la base de conocimiento.
- El esquema de datos queda listo para integracion con LLM/embeddings.

---

## 4. Condicion de Inicio de Fase 3

Fase 3 inicia solo si:
- Se cumplen los criterios de salida de Sprint A y B.
- Existe cobertura automatica del flujo central.
- La automatizacion de recordatorios es estable en ejecucion continua.

---

## 5. Siguientes Acciones Inmediatas

1. Corregir `pipeline.py`.
2. Alinear `api.py` con `core.py`.
3. Externalizar `TELEGRAM_CHAT_ID` y validar configuracion.
4. Agregar pruebas base de pipeline y scheduler.
5. Ejecutar prueba de humo end-to-end con Telegram.
