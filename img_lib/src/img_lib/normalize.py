"""Normalización de Plata (§16): tipos y números de documento, nombres, fechas y códigos
de localidad a un formato único. Las funciones devuelven (valor, causa): `cause` es None
si el valor es válido, o el motivo de rechazo para la tabla de cuarentena.

Los catálogos (tipos de documento, localidades) son PARAMETRIZABLES y los valores por
defecto son ILUSTRATIVOS hasta recibir el diccionario real de las fuentes (PENDIENTE G2)."""
import re
import unicodedata
from datetime import date, datetime

DOC_TYPES = {"CC", "TI", "CE", "RC", "PPT"}  # ILUSTRATIVO
LOCALITIES = {f"{i:02d}" for i in range(1, 21)}  # Bogotá: 20 localidades (ILUSTRATIVO)
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y")


def normalize_doc_type(value, catalog=DOC_TYPES):
    v = re.sub(r"[^A-Z]", "", (value or "").upper())
    return (v, None) if v in catalog else (v or None, "invalid_document_type")


def normalize_doc_number(value):
    v = re.sub(r"[\s.\-]", "", str(value or ""))
    if not v:
        return None, "document_empty"
    if not v.isdigit():
        return v, "document_not_numeric"
    if not 5 <= len(v) <= 12:
        return v, "document_invalid_length"
    return v.lstrip("0") or "0", None


def normalize_name(value):
    """Mayúsculas, sin tildes, espacios colapsados. Conserva la Ñ."""
    if value is None or not str(value).strip():
        return None, "name_empty"
    s = str(value).upper().replace("Ñ", "\0")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s.replace("\0", "Ñ")).strip()
    return s, None


def normalize_date(value, today=None):
    today = today or date.today()
    if value is None or not str(value).strip():
        return None, "date_empty"
    for fmt in _DATE_FORMATS:
        try:
            d = datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
        if d > today or d.year < 1900:
            return d.isoformat(), "date_out_of_range"
        return d.isoformat(), None
    return str(value), "date_invalid_format"


def normalize_locality(value, catalog=LOCALITIES):
    v = re.sub(r"\D", "", str(value or ""))
    if not v:
        return None, "locality_empty"
    v = v.zfill(2)
    return (v, None) if v in catalog else (v, "invalid_locality")
