import re

POLARIDADES_VALIDAS = {"positiva", "negativa", "mixta", "neutra"}

MAX_CHARS_COMENTARIO = 160  # límite del campo comentario en la app
_MARCADORES = re.compile(r"<<<\s*(EVALUACION|FIN)\s*>>>", re.IGNORECASE)
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

def sanear_comentario(texto: str) -> str:
    texto = _MARCADORES.sub(" ", texto)
    texto = _CONTROL.sub(" ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:MAX_CHARS_COMENTARIO]

def filtrar_candidatas(candidatas: list[dict], calificacion: int) -> list[dict]:
    if calificacion >= 4:
        return [c for c in candidatas if c["polaridad"] == "positiva"]
    if calificacion <= 2:
        return [c for c in candidatas if c["polaridad"] == "negativa"]
    return list(candidatas)

def polaridad_por_estrellas(calificacion: int) -> str:
    if calificacion >= 4:
        return "positiva"
    if calificacion <= 2:
        return "negativa"
    return "neutra"

def validar_respuesta(
    etiquetas_modelo: list, polaridad_modelo, candidatas: list[dict], calificacion: int
) -> tuple[list[int], str]:
    permitidos = {c["id"] for c in candidatas}
    etiquetas = []
    for e in etiquetas_modelo:
        try:
            eid = int(e)
        except (TypeError, ValueError):
            continue
        if eid in permitidos and eid not in etiquetas:
            etiquetas.append(eid)
    polaridad = polaridad_modelo if polaridad_modelo in POLARIDADES_VALIDAS else polaridad_por_estrellas(calificacion)
    return etiquetas, polaridad
