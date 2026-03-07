# Sprint D - Busqueda Semantica Hibrida (Local + Nube)

Fecha de definicion: 6 de marzo de 2026
Ventana sugerida de ejecucion: 10 al 24 de marzo de 2026

## 1. Objetivo del Sprint

Implementar el backend `semantic` real para Mitzlia con arquitectura hibrida:
- Opcion local (privacidad y continuidad offline).
- Opcion nube (calidad y escalabilidad inmediata).

El resultado debe mantener el backend `keyword` existente y permitir conmutar sin romper API ni CLI.

## 2. Alcance Tecnico

Incluye:
- Embeddings para notas y consultas.
- Almacenamiento vectorial persistente.
- Indexacion incremental al guardar notas.
- Endpoint de busqueda semantica funcional.
- Evaluacion comparativa local vs nube con metricas.

No incluye en este sprint:
- Generacion de texto con LLM para respuestas largas.
- Agentes autonomos.
- RAG conversacional completo.

## 3. Arquitectura Objetivo

Flujo:
1. Nota guardada -> generar embedding -> guardar vector + metadatos.
2. Consulta usuario -> embedding de consulta -> similarity search.
3. Devolver top-k notas con score.

Componentes:
- `EmbeddingProvider` (interfaz):
  - `LocalEmbeddingProvider` (Ollama)
  - `CloudEmbeddingProvider` (OpenAI)
- `VectorStore` (interfaz):
  - `QdrantVectorStore` (recomendado para inicio)
- `SearchService(backend="semantic")` usando esos adaptadores.

## 4. Opciones Tecnologicas del Sprint D

## Opcion A: Ruta Local
- Embeddings: Ollama (`/api/embed`) con modelo de embeddings local.
- Vector DB: Qdrant local (Docker) o modo embebido para pruebas.

Ventajas:
- Mayor privacidad de datos.
- Puede operar sin internet.
- Costo variable bajo (sin costo por token en nube).

Riesgos:
- Dependencia de hardware local (RAM/CPU/GPU).
- Latencia variable segun equipo.

## Opcion B: Ruta Nube
- Embeddings: OpenAI (`/v1/embeddings`, modelos `text-embedding-3-*`).
- Vector DB: Qdrant local o gestionado.

Ventajas:
- Calidad y estabilidad inmediatas.
- Menor friccion de arranque.

Riesgos:
- Costo por uso.
- Dependencia de conectividad.

## Opcion C: Hibrida (Objetivo recomendado)
- Produccion principal: nube para calidad constante.
- Fallback local: Ollama cuando no hay conectividad o para notas sensibles.

Ventajas:
- Balance entre resiliencia, costo y privacidad.
- Mitiga riesgo de proveedor unico.

## 5. Criterios de Decision (Go/No-Go por backend)

Cada backend se evalua con el mismo set de consultas de prueba:
- Precision@5 (relevancia manual) >= 0.70
- Latencia p95 de consulta <= 1200 ms
- Tasa de error < 2%
- Costo mensual proyectado dentro del presupuesto definido

Regla:
- Si nube supera claramente en calidad y presupuesto lo permite -> nube primaria.
- Si privacidad/continuidad offline es prioritaria -> local primario.
- Si ambas condiciones importan -> hibrido.

## 6. Plan de Implementacion por Semana

## Semana 1 (10-16 marzo 2026)
1. Crear interfaces:
   - `academiaserver/embeddings/base.py`
   - `academiaserver/vectorstore/base.py`
2. Implementar proveedor local (Ollama).
3. Integrar Qdrant local.
4. Extender esquema de nota:
   - `metadata.embedding`: `provider`, `model`, `indexed_at`.
5. Indexacion incremental en `save_idea`.

Entregable:
- `backend=semantic` funcional en modo local.

## Semana 2 (17-24 marzo 2026)
1. Implementar proveedor nube (OpenAI).
2. Conmutacion por configuracion:
   - `SEMANTIC_PROVIDER=local|cloud|hybrid`
3. Fallback automatico (hybrid):
   - nube falla -> local
4. Endpoint y CLI:
   - `GET /search?backend=semantic`
   - `main.py search <query> --backend semantic`
5. Pruebas A/B comparando local vs nube.

Entregable:
- Busqueda semantica hibrida operando con criterios de medicion.

## 7. Configuracion propuesta (.env)

```env
SEMANTIC_PROVIDER=hybrid
SEMANTIC_TOP_K=5

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=embeddinggemma

OPENAI_API_KEY=<tu_api_key>
OPENAI_EMBED_MODEL=text-embedding-3-small

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=academiaserver_notes
```

## 8. Pruebas Minimas Requeridas

1. Unitarias:
- proveedor local retorna vector no vacio
- proveedor nube retorna vector no vacio (mock)
- vectorstore inserta y consulta top-k

2. Integracion:
- guardar nota indexa embedding
- consulta semantica devuelve resultados relevantes
- fallback hibrido funciona cuando falla nube

3. No funcionales:
- benchmark simple (100, 500 y 1000 notas)
- reporte de latencia y precision

## 9. Criterio de Cierre del Sprint D

Sprint D se considera cerrado cuando:
- `backend=semantic` funciona en API y CLI.
- Existe modo local y modo nube documentados y probados.
- El modo hibrido realiza fallback sin perder disponibilidad.
- Se publica reporte de evaluacion con recomendacion final de backend primario.

## 10. Riesgos y Mitigaciones

- Riesgo: baja calidad en español con modelo local.
  - Mitigacion: benchmark con consultas academicas reales y ajuste de modelo.

- Riesgo: costo en nube mayor al esperado.
  - Mitigacion: usar `text-embedding-3-small` para indexacion base y cache local.

- Riesgo: reindexacion lenta.
  - Mitigacion: proceso batch nocturno y cola incremental.
