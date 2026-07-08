from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.clasificacion import filtrar_candidatas, polaridad_por_estrellas, validar_respuesta
from app.infrastructure.llm import ollama

router = APIRouter()

class EtiquetaCandidata(BaseModel):
    id: int
    texto: str
    descripcion: str
    polaridad: Literal["positiva", "negativa"]

class SolicitudClasificacion(BaseModel):
    comentario: str
    rol_evaluado: Literal["conductor", "pasajero"]
    calificacion: int = Field(ge=1, le=5)
    etiquetas_candidatas: list[EtiquetaCandidata]

class RespuestaClasificacion(BaseModel):
    etiquetas: list[int]
    polaridad: Literal["positiva", "negativa", "mixta", "neutra"]

@router.post("/clasificar", response_model=RespuestaClasificacion)
def clasificar(solicitud: SolicitudClasificacion) -> RespuestaClasificacion:
    candidatas = filtrar_candidatas(
        [c.model_dump() for c in solicitud.etiquetas_candidatas], solicitud.calificacion
    )
    if len(solicitud.comentario.strip()) < 10 or not candidatas:
        return RespuestaClasificacion(
            etiquetas=[], polaridad=polaridad_por_estrellas(solicitud.calificacion)
        )
    try:
        crudo = ollama.clasificar_comentario(
            solicitud.comentario, solicitud.rol_evaluado, candidatas
        )
    except ollama.ErrorOllama as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    etiquetas, polaridad = validar_respuesta(
        crudo["etiquetas"], crudo["polaridad"], candidatas, solicitud.calificacion
    )
    return RespuestaClasificacion(etiquetas=etiquetas, polaridad=polaridad)
