from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app import ollama_client
from app.config import settings
from app.clasificacion import (
    filtrar_candidatas,
    polaridad_por_estrellas,
    sanear_comentario,
    validar_respuesta,
)

router = APIRouter()

def verificar_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if settings.llm_jala_api_key and x_api_key != settings.llm_jala_api_key:
        raise HTTPException(status_code=401, detail="API key inválida")

class EtiquetaCandidata(BaseModel):
    id: int
    texto: str
    descripcion: str
    polaridad: Literal["positiva", "negativa"]

class SolicitudClasificacion(BaseModel):
    comentario: str = Field(max_length=5000)
    rol_evaluado: Literal["conductor", "pasajero"]
    calificacion: int = Field(ge=1, le=5)
    etiquetas_candidatas: list[EtiquetaCandidata] = Field(max_length=50)

class RespuestaClasificacion(BaseModel):
    etiquetas: list[int]
    polaridad: Literal["positiva", "negativa", "mixta", "neutra"]

@router.post(
    "/clasificar",
    response_model=RespuestaClasificacion,
    dependencies=[Depends(verificar_api_key)],
)
def clasificar(solicitud: SolicitudClasificacion) -> RespuestaClasificacion:
    candidatas = filtrar_candidatas(
        [c.model_dump() for c in solicitud.etiquetas_candidatas], solicitud.calificacion
    )
    comentario = sanear_comentario(solicitud.comentario)
    if len(comentario) < 10 or not candidatas:
        return RespuestaClasificacion(
            etiquetas=[], polaridad=polaridad_por_estrellas(solicitud.calificacion)
        )
    try:
        crudo = ollama_client.clasificar_comentario(
            comentario, solicitud.rol_evaluado, candidatas
        )
    except ollama_client.ErrorOllama as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    etiquetas, polaridad = validar_respuesta(
        crudo["etiquetas"], crudo["polaridad"], candidatas, solicitud.calificacion
    )
    return RespuestaClasificacion(etiquetas=etiquetas, polaridad=polaridad)
