"""Capa de mapeo entre la base maestra poblacional (columnas RSH_*/SIS_*) y los nombres internos en inglés,
más los catálogos (tipo de documento, sexo, localidad, parentesco, operador) y funciones puras.

Bronce conserva los nombres crudos; Plata ya trabaja con los nombres internos (ver docs/NAMING.md).
Identidad de una persona = tipo + número de documento."""
# ---- columnas de la maestra que usa la PoC (orden de emisión del generador) ----
MASTER_COLUMNS = [
    "RSH_id_llave_maestra", "RSH_id_hogar", "RSH_tip_parentesco", "RSH_tip_documento", "RSH_num_documento",
    "RSH_pri_nombre", "RSH_seg_nombre", "RSH_pri_apellido", "RSH_seg_apellido", "RSH_sexo_persona",
    "RSH_fec_nacimiento", "RSH_grupo_S4", "RSH_vigencia_renec", "SIS_edad", "SIS_cod_loc", "SIS_nom_loc",
    "SIS_bancarizado", "Cuenta1",
]
# base de inhumados (validación): tipo + número y fecha de defunción
DECEASED_COLUMNS = ["RSH_tip_documento", "RSH_num_documento", "fecha_defuncion"]

RSH_TO_INTERNAL = {
    "RSH_id_llave_maestra": "origin_id",
    "RSH_id_hogar": "origin_household_id",
    "RSH_tip_parentesco": "household_role",
    "RSH_tip_documento": "doc_type",
    "RSH_num_documento": "doc_number",
    "RSH_pri_nombre": "first_name",
    "RSH_seg_nombre": "second_name",
    "RSH_pri_apellido": "last_name",
    "RSH_seg_apellido": "second_last_name",
    "RSH_sexo_persona": "sex",
    "RSH_fec_nacimiento": "birth_date",
    "RSH_grupo_S4": "sisben_group",
    "RSH_vigencia_renec": "renec_validity",
    "SIS_edad": "age",
    "SIS_cod_loc": "locality",
    "SIS_nom_loc": "locality_name",
    "SIS_bancarizado": "banked",
    "Cuenta1": "operator",
}
INTERNAL_TO_RSH = {v: k for k, v in RSH_TO_INTERNAL.items()}
DECEASED_TO_INTERNAL = {
    "RSH_tip_documento": "doc_type",
    "RSH_num_documento": "doc_number",
    "fecha_defuncion": "death_date",
}

ADULT_AGE = 18
SEX_WOMAN = "2"
NO_OPERATOR = "SIN OPERADOR"

# ---- catálogos ----
DOC_TYPE_MASTER = {  # maestra: RSH_tip_documento
    0: "No tiene", 1: "Cedula de Ciudadania", 2: "Tarjeta de Identidad", 3: "Cedula de Extranjeria",
    4: "Registro Civil", 5: "DNI (Pais de origen)", 6: "Pasaporte", 7: "Salvoconducto para refugiados",
    8: "Permiso Especial de Permanencia", 9: "Permiso de Proteccion Temporal",
}
DOC_TYPE_ABBREVIATIONS = {"CC": 1, "TI": 2, "CE": 3, "RC": 4, "DNI": 5, "PA": 6, "SC": 7, "PEP": 8, "PPT": 9}
DOC_TYPE_DISPERSAL = {  # listado de dispersión: sdp_tip_documento / sdp_tip_documento_texto
    1: "Registro Civil", 2: "Tarjeta de identidad", 3: "Cedula de Ciudadania", 4: "Cedula de extranjeria",
    5: "DNI (pais de origen)", 6: "Pasaporte", 7: "Salvoconducto para refugiados",
    8: "Permiso especial de permanencia", 9: "Permiso de Proteccion Temporal",
}
# Equivalencia explícita maestra -> listado (distinta codificación: CC y RC no coinciden)
MASTER_TO_DISPERSAL_DOC_TYPE = {1: 3, 2: 2, 3: 4, 4: 1, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
DISPERSAL_TO_MASTER_DOC_TYPE = {v: k for k, v in MASTER_TO_DISPERSAL_DOC_TYPE.items()}

SEX = {1: "Hombre", 2: "Mujer"}
LOCALITY_NO_INFO = 999
LOCALITIES = {  # SIS_cod_loc -> SIS_nom_loc
    1: "USAQUEN", 2: "CHAPINERO", 3: "SANTA FE", 4: "SAN CRISTOBAL", 5: "USME", 6: "TUNJUELITO", 7: "BOSA",
    8: "KENNEDY", 9: "FONTIBON", 10: "ENGATIVA", 11: "SUBA", 12: "BARRIOS UNIDOS", 13: "TEUSAQUILLO",
    14: "MARTIRES", 15: "ANTONIO NARIÑO", 16: "PUENTE ARANDA", 17: "LA CANDELARIA", 18: "RAFAEL URIBE URIBE",
    19: "CIUDAD BOLIVAR", 20: "SUMAPAZ", 999: "ZZ-SIN INFORMACION",
}
HOUSEHOLD_ROLES = {  # RSH_tip_parentesco
    1: "Jefe del hogar", 2: "Conyuge o companero(a)", 3: "Hijo(a), hijastro(a), hijo(a) adoptivo(a)",
    4: "Nieto(a)", 5: "Padre, madre, padrastro, madrastra", 6: "Hermano(a)", 7: "Yerno/Nuera", 8: "Abuelo(a)",
    9: "Suegro(a)", 10: "Tio(a)", 11: "Sobrino(a)", 12: "Primo(a)", 13: "Cunado(a)", 14: "Otro pariente",
    15: "Empleado(a) de servicio domestico", 16: "Pariente del servicio domestico", 17: "Pensionista",
    18: "Pariente de pensionista", 19: "No pariente",
}
GROUP_TARGET = "1. SISBEN IV - A"
SISBEN_GROUPS = ["1. SISBEN IV - A", "2. SISBEN IV - B", "3. SISBEN IV - C", "4. SISBEN IV - D"]
RENEC_VALID_CODES = (0, 12)  # vigente / vigente con pérdida de derechos políticos: no bloquean

# Operador financiero de la maestra (Cuenta1) -> (sdp_operador, sdp_producto = código SIS_banca).
# Diseño: el operador del listado es la entidad que dispersa; el producto sigue el catálogo SIS_banca.
ACCOUNT_OPERATORS = {
    "DAVIPLATA": ("DAVIVIENDA", 1), "NEQUI": ("BANCOLOMBIA", 2), "ALM": ("ALM", 3), "MOVII": ("MOVII", 4),
    "EFECTY": ("EFECTY", 5), "DALE": ("DALE", 6), "POWWI": ("POWII", None),
}
LISTING_NO_INFO_TEXT = "SIN INFORMACION"
LISTING_LOCALITY_NO_INFO_TEXT = "ZZ- SIN INFORMACION"


def blank(value):
    """None, vacío o solo espacios -> None; texto -> sin espacios laterales."""
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def to_int(value):
    """'12', 12, '12.0' -> 12; vacío o no numérico -> None."""
    s = blank(value)
    if s is None:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f == int(f) else None


def doc_type_code(value):
    """Código numérico de la maestra a partir de '1', 1, '1.0' o la sigla ('CC'); None si no se reconoce."""
    s = blank(value)
    if s is None:
        return None
    n = to_int(s)
    if n is not None:
        return n
    return DOC_TYPE_ABBREVIATIONS.get(s.upper())


def doc_type_to_dispersal(master_code):
    """Código de tipo de documento del listado de dispersión; 0 si no hay equivalencia (diccionario)."""
    return MASTER_TO_DISPERSAL_DOC_TYPE.get(to_int(master_code), 0)


def doc_type_dispersal_text(master_code):
    return DOC_TYPE_DISPERSAL.get(doc_type_to_dispersal(master_code), LISTING_NO_INFO_TEXT)


def locality_name(code):
    return LOCALITIES.get(to_int(code))


def listing_locality_name(name):
    """La maestra escribe 'ZZ-SIN INFORMACION'; el listado, 'ZZ- SIN INFORMACION'."""
    n = blank(name)
    if n is None or n.upper().replace(" ", "") == "ZZ-SININFORMACION":
        return LISTING_LOCALITY_NO_INFO_TEXT
    return n.upper()


def operator_to_dispersal(account_operator):
    """(sdp_operador, sdp_producto) de un valor de Cuenta1; (None, None) si no hay operador."""
    return ACCOUNT_OPERATORS.get((blank(account_operator) or "").upper(), (None, None))


def to_internal(row, source):
    """Renombra una fila cruda (RSH_*) a nombres internos. `source` = 'population' o 'validation'.
    Las claves desconocidas (p. ej. `_cycle_id`) se conservan. Los vacíos pasan a None.
    En la base de inhumados no hay llave propia: origin_id = 'INH-<tipo>-<número>'."""
    table = RSH_TO_INTERNAL if source == "population" else DECEASED_TO_INTERNAL
    out = {table.get(k, k): (blank(v) if isinstance(v, str) or v is None else v) for k, v in row.items()}
    if source == "validation":
        out["origin_id"] = f"INH-{out.get('doc_type')}-{out.get('doc_number')}"
    return out
