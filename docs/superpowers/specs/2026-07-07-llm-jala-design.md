# LLM-JALA — Reputación enriquecida (diseño)

**Fecha:** 2026-07-07
**Estado:** aprobado

## Objetivo

Procesar los comentarios de las evaluaciones post-viaje de ViajeSeguro para inferir
**temas** (etiquetas de un catálogo cerrado) y **polaridad**, usando un LLM local
(Ollama), sin APIs externas. Las etiquetas agregadas se muestran en el perfil del
conductor/pasajero cuando alguien decide aceptar o publicar un viaje.

- **Entrada:** comentarios de viajes (texto libre, español mexicano coloquial, con typos).
- **Salida:** etiquetas del catálogo + polaridad (`positiva | negativa | mixta | neutra`).

## Decisiones tomadas

| Decisión | Elección |
|---|---|
| Integración | **API stateless**: LLM-JALA no toca ninguna BD. El job batch vive en el backend. |
| Catálogo de etiquetas | Tabla `etiquetas_catalogo` en la BD del backend (lo define el equipo, editable sin redeploy). El backend manda las candidatas en cada request. |
| Modelo | Ollama local, `qwen2.5:3b`, `temperature 0`, `format json`. |
| Seguridad de contenido | El modelo solo elige de la lista de candidatas; toda salida se valida contra ella. Nunca se muestra texto del usuario ni texto generado. |
| Gate por estrellas | calificación ≥ 4 → solo candidatas positivas; ≤ 2 → solo negativas; 3 → ambas. Se aplica en LLM-JALA. |
| Agregado en perfil | **Top-3** etiquetas por frecuencia sobre las **últimas 20 evaluaciones**; una negativa solo aparece con ≥ 3 ocurrencias en esa ventana. |
| Frecuencia | Job del backend cada 10 min procesa evaluaciones con `nlp_procesado_en IS NULL`. Cada evaluación se clasifica una sola vez. |

## Arquitectura

```
App pasajero/conductor ──evaluación──▶ Backend (tabla evaluaciones)
                                          │ job cada 10 min
                                          ▼
                              POST LLM-JALA /clasificar
                              { comentario, rol_evaluado, calificacion,
                                etiquetas_candidatas: [{id, texto, descripcion, polaridad}] }
                                          │ gate estrellas → prompt cerrado → Ollama
                                          │ validación contra candidatas
                                          ▼
                              { etiquetas: [ids], polaridad }
                                          │
                       Backend: evaluacion_etiquetas + nlp_procesado_en = NOW()
                                          │
        Apps ──al aceptar/publicar──▶ GET top-3 etiquetas agregadas del usuario
```

## Contrato del API

`POST /clasificar`

Request:
```json
{
  "comentario": "me agrado el viaje porque maneja bien y la unidad estaba limpia",
  "rol_evaluado": "conductor",
  "calificacion": 5,
  "etiquetas_candidatas": [
    {"id": 1, "texto": "Buen manejo", "descripcion": "conduce con suavidad y seguridad", "polaridad": "positiva"},
    {"id": 6, "texto": "Manejo brusco", "descripcion": "acelerones, frenados o manejo inseguro", "polaridad": "negativa"}
  ]
}
```

Response `200`:
```json
{ "etiquetas": [1], "polaridad": "positiva" }
```

Reglas:
- Comentario `< 10` caracteres o sin candidatas tras el gate → `etiquetas: []` y
  polaridad derivada de las estrellas, **sin llamar al LLM**.
- Ids devueltos por el modelo que no estén en las candidatas filtradas → se descartan.
- Polaridad inválida del modelo → fallback por estrellas (≥4 positiva, ≤2 negativa, 3 neutra).
- Ollama caído / timeout / respuesta no parseable → `503` (el job del backend reintenta
  en la siguiente corrida).

`GET /health` → estado del servicio y modelo configurado.

## Componentes (fase 1 — este repo)

- `app/domain/clasificacion.py` — lógica pura: gate de estrellas, validación de salida,
  polaridad por estrellas. Sin I/O.
- `app/infrastructure/llm/ollama.py` — construcción del prompt cerrado + cliente HTTP a Ollama.
- `app/infrastructure/api/routers/` — `clasificar` y `health`.
- `docker-compose.yml` — servicio `api` + servicio `ollama` (imagen oficial, volumen para
  modelos, sin exponer a internet en producción).

## Fases

1. **LLM-JALA** (este repo): API + Ollama, demostrable con curl/Insomnia. ← fase actual
2. **Backend**: migración (`etiquetas_catalogo`, `evaluacion_etiquetas`, columna
   `nlp_procesado_en`), job cada 10 min, endpoint top-3 con ventana de 20.
3. **Apps**: chips de etiquetas en aceptar viaje (conductor ve las del pasajero) y en
   asignación de conductor (pasajero ve las del conductor). Si no hay etiquetas o el
   endpoint falla, no se muestran chips.

## Errores y pruebas

- Ningún fallo del LLM afecta el flujo del usuario: el job del backend deja la evaluación
  sin marcar y reintenta.
- Tests unitarios con Ollama mockeado: gate, validación de ids ajenos, comentario corto,
  fallback de polaridad, 503 en fallo.
- Prueba de integración manual con Ollama real: "…no acelebara feo y no me falto al
  respeto" con 5 estrellas debe producir cero etiquetas negativas (ni siquiera fueron
  candidatas).

## Fuera de alcance (por ahora)

- Fine-tuning o embeddings propios (el zero-shot con catálogo cerrado cubre el caso).
- Administración del catálogo desde el panel web (upgrade futuro; por ahora SQL directo).
- Procesamiento en tiempo real por evento (el batch de 10 min es invisible para el usuario).
