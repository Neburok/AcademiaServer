# Arquitectura del Sistema

Este documento describe la arquitectura técnica de **AcademiaServer**, la infraestructura que da soporte al asistente cognitivo **Mitzlia**.

---

# Visión Arquitectónica

El sistema sigue una arquitectura **modular basada en eventos**, diseñada para evolucionar gradualmente desde automatización simple hacia asistentes académicos inteligentes.

Principios fundamentales:

* modularidad
* separación entre datos y lógica
* infraestructura estable antes que complejidad
* evolución incremental

---

# Componentes Principales

## 1. Interfaces de Entrada

Las interfaces permiten al usuario interactuar con el sistema.

Actualmente incluyen:

* Telegram Bot
* CLI (línea de comandos)
* API REST (FastAPI)

Estas interfaces permiten capturar información en lenguaje natural.

---

## 2. Pipeline de Procesamiento

El pipeline es responsable de interpretar y estructurar la información recibida.

Sus funciones incluyen:

* clasificación de notas
* generación automática de títulos
* extracción de metadatos
* detección de recordatorios
* enriquecimiento de información

El pipeline transforma entradas en **notas estructuradas**.

---

## 3. Base de Conocimiento

Las notas procesadas se almacenan como archivos JSON.

Cada nota contiene:

* id
* título
* contenido
* tipo
* etiquetas
* metadatos
* fecha de creación

Esto crea una base de conocimiento **persistente, versionable y portable**.

---

## 4. Scheduler de Eventos

El scheduler es el motor que ejecuta acciones en momentos específicos.

Funciones actuales:

* detección de recordatorios
* ejecución de eventos programados
* envío de notificaciones

Este componente permite que el sistema **actúe automáticamente**.

---

## 5. Sistema de Acciones

Las acciones son respuestas del sistema a eventos detectados.

Ejemplos:

* envío de recordatorios
* generación de resúmenes
* notificaciones al usuario

Este componente representa la capa de **comportamiento activo** del sistema.

---

# Flujo de Información

El flujo principal del sistema es:

Usuario
↓
Interfaz (Telegram / API / CLI)
↓
Pipeline de procesamiento
↓
Base de conocimiento
↓
Scheduler de eventos
↓
Acción automática

Este modelo permite separar claramente:

captura
procesamiento
almacenamiento
ejecución

---

# Evolución Arquitectónica

La arquitectura está diseñada para incorporar nuevas capacidades sin romper la infraestructura existente.

Evoluciones previstas:

* motor de búsqueda semántica
* integración con modelos de lenguaje
* agentes académicos especializados
* análisis de relaciones entre notas

---

# Filosofía del Sistema

La arquitectura de AcademiaServer busca construir una **infraestructura cognitiva personal**.

El objetivo no es solo almacenar información, sino permitir que el sistema:

observe
organice
recuerde
actúe
