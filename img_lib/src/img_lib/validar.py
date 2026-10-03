"""Validaciones de entrada y salida de los cuadernos (§18)."""
from .normalizar import (
    normalizar_documento,
    normalizar_fecha,
    normalizar_localidad,
    normalizar_nombre,
    normalizar_tipo_doc,
)


def validar_registro(reg: dict, hoy=None):
    """Normaliza un registro de persona y devuelve (registro_normalizado, causas).
    `causas` vacío => pasa a Plata; si no, el registro va a calidad.cuarentena."""
    causas = []
    out = {}
    for campo, fn, kw in (
        ("tipo_doc", normalizar_tipo_doc, {}),
        ("num_doc", normalizar_documento, {}),
        ("nombres", normalizar_nombre, {}),
        ("apellidos", normalizar_nombre, {}),
        ("fecha_nacimiento", normalizar_fecha, {"hoy": hoy}),
        ("localidad", normalizar_localidad, {}),
    ):
        if campo not in reg:
            continue
        valor, causa = fn(reg.get(campo), **kw)
        out[campo] = valor
        if causa:
            causas.append(causa)
    return {**reg, **out}, causas


def validar_llaves(filas: list[dict], llaves: list[str]):
    """Salida de un cuaderno: sin nulos en llaves y sin duplicados. Devuelve lista de problemas."""
    problemas, vistos = [], set()
    for i, f in enumerate(filas):
        k = tuple(f.get(c) for c in llaves)
        if any(x is None for x in k):
            problemas.append(f"fila {i}: llave nula {k}")
        if k in vistos:
            problemas.append(f"fila {i}: llave duplicada {k}")
        vistos.add(k)
    return problemas
