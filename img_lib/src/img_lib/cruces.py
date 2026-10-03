"""Etapa 2 (§17): base de cruces. Una fila por persona y por ciclo; registra HECHOS, no decisiones.
Campos de referencia de la Tabla 7 (el documento advierte que los nombres deben ajustarse contra
las variables del manual vigente).

Universo = personas con registro en la fuente poblacional (§17: las poblacionales definen el
universo). Campos sin fuente en la PoC (rol en el hogar, datos financieros) quedan en None: no se
inventan (PENDIENTE G2)."""


def primera_por_persona(filas):
    por = {}
    for f in sorted(filas, key=lambda r: r["id_origen"]):
        por.setdefault(f["id_persona"], f)
    return por


def construir_base(pob_oro, val_oro, *, id_ciclo, fecha_corte, version_fuentes, id_ejecucion,
                   version_cuaderno, ts):
    """`pob_oro` / `val_oro`: filas de lh_oro.fuentes.*_corte (con id_persona e id_hogar).
    `version_fuentes`: {"poblacional": ..., "validacion": ...}. Devuelve filas de cruces.base_cruces."""
    pob = primera_por_persona(pob_oro)
    val = primera_por_persona(val_oro)
    base = []
    for id_persona in sorted(pob):
        p, v = pob[id_persona], val.get(id_persona)
        base.append({
            # Ciclo
            "id_ciclo": id_ciclo, "fecha_corte": fecha_corte,
            "version_fuente_poblacional": version_fuentes.get("poblacional"),
            "version_fuente_validacion": version_fuentes.get("validacion"),
            # Persona
            "id_persona": id_persona, "tipo_doc": p["tipo_doc"], "num_doc": p["num_doc"],
            "nombres": p["nombres"], "apellidos": p["apellidos"], "fecha_nacimiento": p["fecha_nacimiento"],
            # Hogar y ubicación (rol_hogar: sin fuente definida en la PoC)
            "id_hogar": p["id_hogar"], "rol_hogar": None, "localidad": p["localidad"],
            "direccion": p.get("direccion"),
            # Clasificación socioeconómica
            "grupo_sisben": p.get("grupo_sisben"), "subgrupo_sisben": p.get("subgrupo_sisben"),
            "fecha_encuesta": p.get("fecha_encuesta"),
            # Marcas de validación: encontrado (sí/no), valor reportado y fecha de corte
            "encontrado_validacion": "SI" if v else "NO",
            "valor_validacion": v["estado"] if v else None,
            "fecha_corte_validacion": v["fecha_corte"] if v else None,
            # Datos financieros: sin fuente financiera en la PoC
            "operador": None, "tipo_producto": None, "estado_producto": None,
            # Trazabilidad
            "id_ejecucion": id_ejecucion, "version_cuaderno": version_cuaderno, "ts_proceso": ts,
        })
    return base


def pct_coincidencia(base):
    """Insumo del Control 2: % de personas del universo encontradas en la fuente de validación."""
    if not base:
        return 0.0
    return 100.0 * sum(1 for r in base if r["encontrado_validacion"] == "SI") / len(base)
