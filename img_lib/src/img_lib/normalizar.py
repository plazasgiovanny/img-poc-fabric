"""Normalización de Plata (§16): tipos y números de documento, nombres, fechas y códigos
de localidad a un formato único. Las funciones devuelven (valor, causa): `causa` es None
si el valor es válido, o el motivo de rechazo para la tabla de cuarentena.

Los catálogos (tipos de documento, localidades) son PARAMETRIZABLES y los valores por
defecto son ILUSTRATIVOS hasta recibir el diccionario real de las fuentes (PENDIENTE G2)."""
import re
import unicodedata
from datetime import date, datetime

TIPOS_DOC = {"CC", "TI", "CE", "RC", "PPT"}  # ILUSTRATIVO
LOCALIDADES = {f"{i:02d}" for i in range(1, 21)}  # Bogotá: 20 localidades (ILUSTRATIVO)
_FORMATOS_FECHA = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y")


def normalizar_tipo_doc(valor, catalogo=TIPOS_DOC):
    v = re.sub(r"[^A-Z]", "", (valor or "").upper())
    return (v, None) if v in catalogo else (v or None, "tipo_documento_invalido")


def normalizar_documento(valor):
    v = re.sub(r"[\s.\-]", "", str(valor or ""))
    if not v:
        return None, "documento_vacio"
    if not v.isdigit():
        return v, "documento_no_numerico"
    if not 5 <= len(v) <= 12:
        return v, "documento_longitud_invalida"
    return v.lstrip("0") or "0", None


def normalizar_nombre(valor):
    """Mayúsculas, sin tildes, espacios colapsados. Conserva la Ñ."""
    if valor is None or not str(valor).strip():
        return None, "nombre_vacio"
    s = str(valor).upper().replace("Ñ", "\0")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s.replace("\0", "Ñ")).strip()
    return s, None


def normalizar_fecha(valor, hoy=None):
    hoy = hoy or date.today()
    if valor is None or not str(valor).strip():
        return None, "fecha_vacia"
    for fmt in _FORMATOS_FECHA:
        try:
            d = datetime.strptime(str(valor).strip(), fmt).date()
        except ValueError:
            continue
        if d > hoy or d.year < 1900:
            return d.isoformat(), "fecha_fuera_de_rango"
        return d.isoformat(), None
    return str(valor), "fecha_formato_invalido"


def normalizar_localidad(valor, catalogo=LOCALIDADES):
    v = re.sub(r"\D", "", str(valor or ""))
    if not v:
        return None, "localidad_vacia"
    v = v.zfill(2)
    return (v, None) if v in catalogo else (v, "localidad_invalida")
