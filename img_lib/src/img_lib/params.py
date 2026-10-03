"""Lectura de parámetros vigentes (§18): cada parámetro tiene vigencia (desde/hasta),
responsable y documento soporte. Los criterios son datos, no código."""
from datetime import date


def _a_fecha(v):
    if v is None or v == "":
        return None
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def vigentes(filas: list[dict], fecha_corte) -> list[dict]:
    """Filtra `filas` (dicts con vigente_desde / vigente_hasta) vigentes en `fecha_corte`.
    `vigente_hasta` nulo = sin fecha de fin. Los parámetros aplicados deben registrarse
    en la bitácora y en el informe de generación."""
    corte = _a_fecha(fecha_corte)
    res = []
    for f in filas:
        desde, hasta = _a_fecha(f.get("vigente_desde")), _a_fecha(f.get("vigente_hasta"))
        if desde and desde > corte:
            continue
        if hasta and hasta < corte:
            continue
        res.append(f)
    return res


def hay_ilustrativos(filas: list[dict]) -> bool:
    """True si algún parámetro aplicado es ILUSTRATIVO (debe verse en el informe, R8)."""
    return any(int(f.get("es_ilustrativo", 0) or 0) == 1 for f in filas)
