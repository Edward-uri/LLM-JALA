import pytest
from fastapi.testclient import TestClient

from app.infrastructure.llm import ollama
from app.main import app

cliente = TestClient(app)

CANDIDATAS = [
    {"id": 1, "texto": "Buen manejo", "descripcion": "conduce con suavidad", "polaridad": "positiva"},
    {"id": 2, "texto": "Unidad limpia", "descripcion": "vehículo limpio", "polaridad": "positiva"},
    {"id": 6, "texto": "Manejo brusco", "descripcion": "acelerones o frenados", "polaridad": "negativa"},
]

def _solicitud(**cambios):
    base = {
        "comentario": "me agrado el viaje porque maneja bien y la unidad estaba limpia",
        "rol_evaluado": "conductor",
        "calificacion": 5,
        "etiquetas_candidatas": CANDIDATAS,
    }
    base.update(cambios)
    return base

def test_health():
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ok"

def test_clasificar_filtra_salida_del_modelo(monkeypatch):
    # el modelo alucina el id 6 (negativa): con 5 estrellas nunca fue candidata
    monkeypatch.setattr(
        ollama, "clasificar_comentario",
        lambda *a, **k: {"etiquetas": [1, 2, 6, 42], "polaridad": "positiva"},
    )
    respuesta = cliente.post("/clasificar", json=_solicitud())
    assert respuesta.status_code == 200
    assert respuesta.json() == {"etiquetas": [1, 2], "polaridad": "positiva"}

def test_comentario_corto_no_llama_al_llm(monkeypatch):
    def explota(*a, **k):
        raise AssertionError("no debía llamar a Ollama")
    monkeypatch.setattr(ollama, "clasificar_comentario", explota)
    respuesta = cliente.post("/clasificar", json=_solicitud(comentario="ok"))
    assert respuesta.status_code == 200
    assert respuesta.json() == {"etiquetas": [], "polaridad": "positiva"}

def test_sin_candidatas_tras_gate_no_llama_al_llm(monkeypatch):
    def explota(*a, **k):
        raise AssertionError("no debía llamar a Ollama")
    monkeypatch.setattr(ollama, "clasificar_comentario", explota)
    solo_positivas = [c for c in CANDIDATAS if c["polaridad"] == "positiva"]
    respuesta = cliente.post(
        "/clasificar",
        json=_solicitud(calificacion=1, etiquetas_candidatas=solo_positivas,
                        comentario="me dejo esperando veinte minutos"),
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"etiquetas": [], "polaridad": "negativa"}

def test_ollama_caido_responde_503(monkeypatch):
    def falla(*a, **k):
        raise ollama.ErrorOllama("connection refused")
    monkeypatch.setattr(ollama, "clasificar_comentario", falla)
    respuesta = cliente.post("/clasificar", json=_solicitud())
    assert respuesta.status_code == 503

@pytest.mark.parametrize("calificacion", [0, 6])
def test_calificacion_fuera_de_rango_es_422(calificacion):
    respuesta = cliente.post("/clasificar", json=_solicitud(calificacion=calificacion))
    assert respuesta.status_code == 422
