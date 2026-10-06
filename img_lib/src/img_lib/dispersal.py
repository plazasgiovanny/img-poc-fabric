"""Listado de dispersión por operador (diccionario de listados de dispersión): 32 columnas en orden, con los
valores por defecto del diccionario cuando falta el dato, y archivo .xlsx (openpyxl, importación diferida).

Identificadores generados de forma determinista a partir de cycle_id y del número de fila `seq` del ciclo
(`cycle_key` = los dígitos de cycle_id, p. ej. '2026-09' -> 202609):
  sdp_id_listado = int('1' + cycle_key + seq a 6 dígitos)      sdp_id_IMG = int('2' + cycle_key + seq a 6 dígitos)
  sdp_id_pago    = 'IMG-<cycle_key>-<seq a 6 dígitos>'          sdp_Giro   = int(cycle_key + '01')  (una dispersión)"""
import io
import re

from . import mapping

COLUMNS = [
    "sdp_id_listado", "sdp_id_pago", "sdp_id_IMG", "sdp_programa_IMG", "sdp_Giro", "sdp_id_llave_maestra",
    "sdp_id_llave_maestra_estu", "sdp_tipoBeneficiario", "sdp_Id", "sdp_tip_documento", "sdp_tip_documento_texto",
    "sdp_num_documento", "sdp_pri_nombre", "sdp_seg_nombre", "sdp_pri_apellido", "sdp_seg_apellido",
    "sdp_vigencia_renec", "sdp_Edad", "sdp_sexo_persona", "sdp_cod_localidad", "sdp_localidad", "sdp_cod_upz",
    "sdp_upz", "sdp_hog_grupo", "sdp_puntajesisben3", "sdp_hog_clasificacion", "sdp_operador", "sdp_producto",
    "sdp_ncuenta", "sdp_cel_beneficiario_origen", "sdp_monto", "parqueadero",
]
PROGRAM = "TI-Transferencias para la Inclusión"


def cycle_key(cycle_id):
    digits = re.sub(r"\D", "", str(cycle_id))
    if not digits:
        raise ValueError(f"cycle_id without digits: {cycle_id!r}")
    return digits


def listing_ids(cycle_id, seq):
    key = cycle_key(cycle_id)
    return {"sdp_id_listado": int(f"1{key}{seq:06d}"), "sdp_id_pago": f"IMG-{key}-{seq:06d}",
            "sdp_id_IMG": int(f"2{key}{seq:06d}"), "sdp_Giro": int(f"{key}01")}


def _upper(value):
    return (str(value).upper().strip() or None) if value not in (None, "") else None


def to_dispersal_row(row):
    """Fila del listado (32 columnas) a partir de una fila de la sábana de pagos (nombres internos)."""
    ids = listing_ids(row["cycle_id"], int(row["seq"]))
    llave = mapping.to_int(row.get("origin_id"))
    out = {
        **ids, "sdp_programa_IMG": PROGRAM,
        "sdp_id_llave_maestra": llave, "sdp_id_llave_maestra_estu": llave,
        "sdp_tipoBeneficiario": None, "sdp_Id": None,
        "sdp_tip_documento": mapping.doc_type_to_dispersal(row.get("doc_type")),
        "sdp_tip_documento_texto": mapping.doc_type_dispersal_text(row.get("doc_type")),
        "sdp_num_documento": mapping.to_int(row.get("doc_number")) or 0,
        "sdp_pri_nombre": _upper(row.get("first_name")), "sdp_seg_nombre": _upper(row.get("second_name")),
        "sdp_pri_apellido": _upper(row.get("last_name")), "sdp_seg_apellido": _upper(row.get("second_last_name")),
        "sdp_vigencia_renec": mapping.to_int(row.get("renec_validity")),
        "sdp_Edad": mapping.to_int(row.get("age")),
        "sdp_sexo_persona": mapping.to_int(row.get("sex")),
        "sdp_cod_localidad": mapping.to_int(row.get("locality")) or mapping.LOCALITY_NO_INFO,
        "sdp_localidad": mapping.listing_locality_name(row.get("locality_name")),
        "sdp_cod_upz": 999, "sdp_upz": mapping.LISTING_LOCALITY_NO_INFO_TEXT,
        "sdp_hog_grupo": None, "sdp_puntajesisben3": None, "sdp_hog_clasificacion": None,
        "sdp_operador": _upper(row.get("operator")), "sdp_producto": row.get("product"),
        "sdp_ncuenta": 0, "sdp_cel_beneficiario_origen": 0,
        "sdp_monto": row.get("amount"), "parqueadero": mapping.LISTING_NO_INFO_TEXT,
    }
    return {c: out[c] for c in COLUMNS}


def xlsx_bytes(rows, sheet_title="listado"):
    """Libro .xlsx con los 32 encabezados y una fila por beneficiario (rows = filas de to_dispersal_row)."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(COLUMNS)
    for r in rows:
        ws.append([r[c] for c in COLUMNS])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
