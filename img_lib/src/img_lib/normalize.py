"""Normalización de Plata (§16): tipos y números de documento, nombres, fechas, sexo, edad y códigos
de localidad a un formato único. Las funciones devuelven (valor, causa): `cause` es None
si el valor es válido, o el motivo de rechazo para la tabla de cuarentena.

Los catálogos son los de la base maestra (ver `mapping`) y son parametrizables."""
import re
import unicodedata
from datetime import date, datetime

from . import mapping

DOC_TYPES = {str(c) for c in mapping.DOC_TYPE_MASTER if c != 0}  # '0' = «No tiene»: no identifica a nadie
LOCALITIES = {str(c) for c in mapping.LOCALITIES}  # 1-20 y 999 (sin información)
SEXES = {str(c) for c in mapping.SEX}
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y")


def normalize_doc_type(value, catalog=DOC_TYPES):
    """Código numérico de la maestra como texto ('1'..'9'). Acepta también la sigla (CC, TI...)."""
    code = mapping.doc_type_code(value)
    v = None if code is None else str(code)
    return (v, None) if v in catalog else (v, "invalid_document_type")


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


def normalize_optional_name(value):
    """Segundo nombre / segundo apellido: vacío es válido."""
    if value is None or not str(value).strip():
        return None, None
    return normalize_name(value)


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
    """Código de localidad sin ceros a la izquierda ('1'..'20'); 999 = sin información."""
    n = mapping.to_int(re.sub(r"\D", "", str(value or "")))
    if n is None:
        return None, "locality_empty"
    v = str(n)
    return (v, None) if v in catalog else (v, "invalid_locality")


def normalize_sex(value, catalog=SEXES):
    n = mapping.to_int(value)
    v = None if n is None else str(n)
    return (v, None) if v in catalog else (v, "invalid_sex")


def normalize_age(value):
    n = mapping.to_int(value)
    if n is None:
        return None, "age_invalid"
    return (n, None) if 0 <= n <= 120 else (n, "age_out_of_range")


def normalize_banked(value):
    """SIS_bancarizado: 1 = tiene operador activo; vacío = 0."""
    n = mapping.to_int(value)
    return (1 if n == 1 else 0), None


def normalize_renec(value):
    """Código de vigencia RENEC como texto. Vacío = None (no bloquea); no numérico = rechazo."""
    if value is None or not str(value).strip():
        return None, None
    n = mapping.to_int(value)
    return (None, "invalid_renec_code") if n is None else (str(n), None)
