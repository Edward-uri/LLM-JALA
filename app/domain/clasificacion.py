"""Lógica pura de clasificación: gate por estrellas y validación de la salida del LLM."""

POLARIDADES_VALIDAS = {"positiva", "negativa", "mixta", "neutra"}

def filtrar_candidatas(candidatas: list[dict], calificacion: int) -> list[dict]:
    """Gate por estrellas: >=4 solo positivas, <=2 solo negativas, 3 ambas."""
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
    """Filtra la salida del LLM: solo ids presentes en las candidatas; polaridad
    inválida cae al fallback por estrellas."""
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
