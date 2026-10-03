"""Lectura de parámetros vigentes (§18): cada parámetro tiene vigencia (desde/hasta),
responsable y documento soporte. Los criterios son datos, no código."""
from datetime import date


def _to_date(v):
    if v is None or v == "":
        return None
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def active(rows: list[dict], cutoff_date) -> list[dict]:
    """Filtra `rows` (dicts con valid_from / valid_to) vigentes en `cutoff_date`.
    `valid_to` nulo = sin fecha de fin. Los parámetros aplicados deben registrarse
    en la bitácora y en el informe de generación."""
    cutoff = _to_date(cutoff_date)
    res = []
    for f in rows:
        start_date, end_date = _to_date(f.get("valid_from")), _to_date(f.get("valid_to"))
        if start_date and start_date > cutoff:
            continue
        if end_date and end_date < cutoff:
            continue
        res.append(f)
    return res


def has_illustrative(rows: list[dict]) -> bool:
    """True si algún parámetro aplicado es ILUSTRATIVO (debe verse en el informe, R8)."""
    return any(int(f.get("is_illustrative", 0) or 0) == 1 for f in rows)
