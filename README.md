# LLM-JALA

Microservicio NLP de **reputación enriquecida** para ViajeSeguro: recibe el comentario
de una evaluación post-viaje y devuelve **temas** (etiquetas de un catálogo cerrado que
manda el backend) y **polaridad**, usando un LLM local vía Ollama. Sin APIs externas.

Diseño completo: [docs/superpowers/specs/2026-07-07-llm-jala-design.md](docs/superpowers/specs/2026-07-07-llm-jala-design.md)

## Correr local

```bash
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:3b   # solo la primera vez
```

## Probar

```bash
curl -s http://localhost:8100/clasificar -X POST -H 'Content-Type: application/json' -d '{
  "comentario": "me agrado el viaje porque maneja bien y la unidad estaba limpia, no acelebara feo y no me falto al respeto",
  "rol_evaluado": "conductor",
  "calificacion": 5,
  "etiquetas_candidatas": [
    {"id": 1, "texto": "Buen manejo", "descripcion": "conduce con suavidad y seguridad", "polaridad": "positiva"},
    {"id": 2, "texto": "Unidad limpia", "descripcion": "el vehículo estaba limpio y en buen estado", "polaridad": "positiva"},
    {"id": 3, "texto": "Trato amable", "descripcion": "fue cortés, respetuoso y agradable", "polaridad": "positiva"},
    {"id": 6, "texto": "Manejo brusco", "descripcion": "acelerones, frenados o manejo inseguro", "polaridad": "negativa"}
  ]
}'
# → {"etiquetas": [1, 2, 3], "polaridad": "positiva"}
```

Reglas clave: el gate por estrellas descarta candidatas de la polaridad contraria
(≥4 solo positivas, ≤2 solo negativas, 3 ambas); todo id que el modelo devuelva fuera
de las candidatas se filtra; si Ollama está caído responde `503` y el job del backend
reintenta después.

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```
