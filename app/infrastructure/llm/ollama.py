"""Cliente de Ollama: arma el prompt cerrado y parsea la respuesta JSON del modelo."""
import json

import httpx

from app.config import settings

class ErrorOllama(Exception):
    """Ollama no disponible o respuesta no parseable. El caller responde 503."""

PROMPT_SISTEMA = (
    "Eres un clasificador de evaluaciones de una app de viajes. Recibes la evaluación "
    "que un usuario escribió sobre un {rol} en español mexicano coloquial (puede tener "
    "errores de ortografía). Responde ÚNICAMENTE un JSON con este formato: "
    '{{"etiquetas": [ids], "polaridad": "positiva" | "negativa" | "mixta" | "neutra"}}. '
    'En "etiquetas" pon SOLO los ids de la lista permitida que el texto respalda '
    "claramente; si ninguna aplica pon []. No inventes ids. Ojo con las negaciones: "
    '"no manejaba feo" NO respalda una etiqueta de mal manejo. En "polaridad" clasifica '
    "el sentimiento general del comentario.\n"
    "Lista permitida:\n{lista}"
)

def clasificar_comentario(comentario: str, rol_evaluado: str, candidatas: list[dict]) -> dict:
    lista = "\n".join(f"- {c['id']}: {c['texto']} — {c['descripcion']}" for c in candidatas)
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA.format(rol=rol_evaluado, lista=lista)},
            {"role": "user", "content": comentario},
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0},
    }
    try:
        respuesta = httpx.post(
            f"{settings.ollama_url}/api/chat", json=payload, timeout=settings.ollama_timeout_s
        )
        respuesta.raise_for_status()
    except httpx.HTTPError as exc:
        raise ErrorOllama(f"Ollama no disponible: {exc}") from exc
    try:
        datos = json.loads(respuesta.json()["message"]["content"])
        return {
            "etiquetas": datos.get("etiquetas", []),
            "polaridad": datos.get("polaridad"),
        }
    except (KeyError, ValueError, TypeError) as exc:
        raise ErrorOllama(f"Respuesta del modelo no parseable: {exc}") from exc
