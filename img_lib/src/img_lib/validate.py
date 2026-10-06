"""Validaciones de entrada y salida de los cuadernos (§18)."""
from .normalize import (
    normalize_age,
    normalize_banked,
    normalize_date,
    normalize_doc_number,
    normalize_doc_type,
    normalize_locality,
    normalize_name,
    normalize_optional_name,
    normalize_renec,
    normalize_sex,
)

_FIELDS = (
    ("doc_type", normalize_doc_type, {}),
    ("doc_number", normalize_doc_number, {}),
    ("first_name", normalize_name, {}),
    ("second_name", normalize_optional_name, {}),
    ("last_name", normalize_name, {}),
    ("second_last_name", normalize_optional_name, {}),
    ("birth_date", normalize_date, {"today": "today"}),
    ("death_date", normalize_date, {"today": "today"}),
    ("sex", normalize_sex, {}),
    ("age", normalize_age, {}),
    ("locality", normalize_locality, {}),
    ("banked", normalize_banked, {}),
    ("renec_validity", normalize_renec, {}),
)


def validate_record(rec: dict, today=None):
    """Normaliza un registro de persona (nombres internos) y devuelve (normalized_record, causes).
    `causes` vacío => pasa a Plata; si no, el registro va a quality.quarantine.
    Solo se validan los campos presentes: la base de inhumados trae tipo, número y fecha de defunción."""
    causes = []
    out = {}
    for field, fn, kw in _FIELDS:
        if field not in rec:
            continue
        value, cause = fn(rec.get(field), **{k: today for k in kw})
        out[field] = value
        if cause:
            causes.append(cause)
    out = {**rec, **out}
    if "first_name" in out:  # nombres completos (Tabla 7), a partir de las partes ya normalizadas
        out["first_names"] = " ".join(p for p in (out.get("first_name"), out.get("second_name")) if p) or None
        out["last_names"] = " ".join(p for p in (out.get("last_name"), out.get("second_last_name")) if p) or None
    return out, causes


def validate_keys(rows: list[dict], keys: list[str]):
    """Salida de un cuaderno: sin nulos en llaves y sin duplicados. Devuelve lista de problemas."""
    problems, seen = [], set()
    for i, f in enumerate(rows):
        k = tuple(f.get(c) for c in keys)
        if any(x is None for x in k):
            problems.append(f"row {i}: null key {k}")
        if k in seen:
            problems.append(f"row {i}: duplicate key {k}")
        seen.add(k)
    return problems
