# AcademiaServer

Infraestructura para **Mitzlia**, un asistente cognitivo académico diseñado para amplificar la gestión del conocimiento personal.

AcademiaServer proporciona la arquitectura base que permite capturar ideas, organizar conocimiento, ejecutar recordatorios y evolucionar gradualmente hacia un sistema académico asistido por inteligencia artificial.

---

# 🐈‍⬛ Mitzlia

**Mitzlia** es un asistente inteligente inspirado en *miztli*, el gato en la tradición náhuatl, símbolo de observación silenciosa, agilidad mental y sabiduría estratégica.

Al igual que el gato, Mitzlia observa, recuerda y actúa en el momento adecuado.

Su objetivo es ayudar al usuario a:

* capturar ideas rápidamente
* organizar conocimiento académico
* recordar eventos importantes
* conectar conceptos y proyectos
* transformar pensamientos en acciones útiles

Mitzlia funciona como un **segundo cerebro digital**, diseñado para acompañar procesos de investigación, docencia y producción intelectual.

Más información en:

MITZLIA.md

---

# Visión

AcademiaServer es una infraestructura académica personal diseñada para apoyar de manera estructurada:

* investigación
* docencia
* escritura académica
* experimentación con inteligencia artificial

El proyecto busca evolucionar desde un sistema de captura de ideas hacia un **laboratorio digital académico autónomo**.

La filosofía de desarrollo prioriza:

* estabilidad antes que complejidad
* infraestructura antes que automatización
* automatización antes que autonomía

---

# Propósito del Sistema

AcademiaServer no es simplemente una aplicación de notas ni un bot aislado.

Funciona como:

1. Inbox académico persistente
2. Sistema estructurado de captura de conocimiento
3. Pipeline de procesamiento de notas
4. Motor de eventos y recordatorios
5. Base para asistentes académicos inteligentes

En conjunto, estos componentes conforman una **infraestructura cognitiva personal**.

---

# Estado Actual del Proyecto

Actualmente el sistema permite:

* Captura de ideas y notas desde Telegram
* Interpretación básica de lenguaje natural
* Estructuración automática de notas
* Almacenamiento de conocimiento en formato JSON
* Detección automática de recordatorios
* Sistema de eventos basado en scheduler
* Envío de notificaciones automáticas al usuario

Estas capacidades constituyen la primera versión funcional de **Mitzlia**.

---

# Arquitectura General

El sistema sigue una arquitectura modular basada en procesamiento de eventos.

Flujo simplificado:

Usuario
↓
Telegram
↓
Pipeline de procesamiento
↓
Base de conocimiento (JSON)
↓
Scheduler de eventos
↓
Acciones automáticas (recordatorios)

Este enfoque permite separar claramente:

* captura de información
* procesamiento
* almacenamiento
* ejecución de acciones

---

# Estructura del Proyecto

```
academiaserver/
    core/              lógica central del sistema
    processing/        pipeline de procesamiento de notas
    scheduler/         motor de eventos y recordatorios
    clients/           interfaces externas (Telegram, API)

inbox/
    base de conocimiento en formato JSON

logs/
    registro de actividad del sistema

docs/
    documentación técnica
```

---

# Filosofía Arquitectónica

El sistema está diseñado bajo los siguientes principios:

Servidor ligero siempre activo
Mini-PC como nodo central de procesamiento.

Modularidad
Los componentes se desarrollan como módulos independientes.

Separación entre datos y lógica
El conocimiento se almacena como datos estructurados.

Control de versiones
Todo el sistema evoluciona bajo control de Git.

Evolución incremental
Cada nueva capacidad se construye sobre una base estable.

---

# Roadmap del Proyecto

## Fase 1 – Infraestructura Fundacional

* estructura del repositorio
* sistema de registro
* captura básica de ideas
* almacenamiento estructurado

## Fase 2 – Automatización

* clasificación de notas
* pipeline de procesamiento
* scheduler de recordatorios
* integración con Telegram

## Fase 3 – Inteligencia Asistida

* enriquecimiento semántico de notas
* búsqueda avanzada de conocimiento
* generación de resúmenes

## Fase 4 – Asistente Cognitivo

* análisis de relaciones entre ideas
* organización automática de proyectos
* asistencia en investigación académica

## Fase 5 – Laboratorio de IA

* agentes académicos especializados
* experimentación con modelos de lenguaje
* automatización avanzada de flujos de trabajo

---

# Objetivo a Largo Plazo

Evolucionar AcademiaServer hacia un **laboratorio cognitivo académico**, donde Mitzlia funcione como un asistente capaz de:

* organizar conocimiento académico
* relacionar ideas y proyectos
* asistir procesos de investigación
* apoyar desarrollo curricular
* colaborar en escritura académica
* facilitar experimentación con inteligencia artificial

Mitzlia no pretende reemplazar el pensamiento humano.

Su propósito es **amplificarlo**.

---

# Principio Fundamental

- Mitzlia observa.
- Mitzlia recuerda.
- Mitzlia actúa cuando es necesario.
