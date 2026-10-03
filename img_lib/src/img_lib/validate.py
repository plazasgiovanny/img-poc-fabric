"""Validaciones de entrada y salida de los cuadernos (§18)."""
from .normalize import (
    normalize_date,
    normalize_doc_number,
    normalize_doc_type,
    normalize_locality,
    normalize_name,
)


def validate_record(rec: dict, today=None):
    """Normaliza un registro de persona y devuelve (normalized_record, causas).
    `causes` vacío => pasa a Plata; si no, el registro va a quality.quarantine."""
    causes = []
    out = {}
    for field, fn, kw in (
        ("doc_type", normalize_doc_type, {}),
        ("doc_number", normalize_doc_number, {}),
        ("first_names", normalize_name, {}),
        ("last_names", normalize_name, {}),
        ("birth_date", normalize_date, {"today": today}),
        ("locality", normalize_locality, {}),
    ):
        if field not in rec:
            continue
        value, cause = fn(rec.get(field), **kw)
        out[field] = value
        if cause:
            causes.append(cause)
    return {**rec, **out}, causes


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
