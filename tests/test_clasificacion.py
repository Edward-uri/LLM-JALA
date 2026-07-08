from app.domain.clasificacion import filtrar_candidatas, polaridad_por_estrellas, validar_respuesta

CANDIDATAS = [
    {"id": 1, "texto": "Buen manejo", "descripcion": "conduce con suavidad", "polaridad": "positiva"},
    {"id": 2, "texto": "Unidad limpia", "descripcion": "vehículo limpio", "polaridad": "positiva"},
    {"id": 6, "texto": "Manejo brusco", "descripcion": "acelerones o frenados", "polaridad": "negativa"},
]

def test_gate_5_estrellas_solo_positivas():
    assert {c["id"] for c in filtrar_candidatas(CANDIDATAS, 5)} == {1, 2}

def test_gate_1_estrella_solo_negativas():
    assert {c["id"] for c in filtrar_candidatas(CANDIDATAS, 1)} == {6}

def test_gate_3_estrellas_todas():
    assert len(filtrar_candidatas(CANDIDATAS, 3)) == 3

def test_polaridad_por_estrellas():
    assert polaridad_por_estrellas(5) == "positiva"
    assert polaridad_por_estrellas(2) == "negativa"
    assert polaridad_por_estrellas(3) == "neutra"

def test_validar_descarta_ids_ajenos_y_duplicados():
    etiquetas, _ = validar_respuesta([1, 99, "2", 1, "x"], "positiva", CANDIDATAS, 5)
    assert etiquetas == [1, 2]

def test_validar_polaridad_invalida_cae_a_estrellas():
    _, polaridad = validar_respuesta([], "buenisima", CANDIDATAS, 5)
    assert polaridad == "positiva"
    _, polaridad = validar_respuesta([], None, CANDIDATAS, 1)
    assert polaridad == "negativa"
