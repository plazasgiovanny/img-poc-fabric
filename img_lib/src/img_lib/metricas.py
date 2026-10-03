"""Métricas del Experimento 2 (§7): errores <1 %, auditoría 100 %.

La comparación es contra la VERDAD CONOCIDA del generador sintético, no contra el manual."""


def tasa_error_cuarentena(verdad, ids_en_cuarentena):
    """verdad: filas con fuente, id_origen, va_a_cuarentena. ids_en_cuarentena: {(fuente, id_origen)}."""
    esperados = {(v["fuente"], v["id_origen"]) for v in verdad if int(v["va_a_cuarentena"])}
    return len(esperados ^ set(ids_en_cuarentena)) / max(len(verdad), 1)


def tasa_error_mdm(verdad, xref):
    """Personas distintas unidas (falso positivo) + una persona partida (falso negativo), sobre
    el total de personas reales."""
    v = {(x["fuente"], x["id_origen"]): x["id_persona_real"] for x in verdad}
    por_maestro, por_real = {}, {}
    for x in xref:
        real = v[(x["fuente"], x["id_origen"])]
        por_maestro.setdefault(x["id_persona"], set()).add(real)
        por_real.setdefault(real, set()).add(x["id_persona"])
    errores = sum(len(s) > 1 for s in por_maestro.values()) + sum(len(s) > 1 for s in por_real.values())
    return errores / max(len(por_real), 1)


def tasa_error_bloqueo(verdad, xref, focalizacion, esperado, causales_bloqueo):
    """Compara las causales de bloqueo aplicadas con las esperadas según la verdad conocida.

    `esperado(info) -> set de causales`, con info = {"fallecido": bool, "en_validacion": bool}
    de la persona real. Solo cuentan las causales de `causales_bloqueo` (las reglas vigentes), así
    no se mezclan con las de focalización. Tasa = filas con causales distintas / filas evaluadas."""
    info = {}
    for x in verdad:
        r = info.setdefault(x["id_persona_real"], {"fallecido": False, "en_validacion": False})
        r["fallecido"] |= x["estado_real"] == "FALLECIDO"
        r["en_validacion"] |= x["fuente"] == "validacion"
    real_de = {}
    v = {(x["fuente"], x["id_origen"]): x["id_persona_real"] for x in verdad}
    for x in xref:
        real_de.setdefault(x["id_persona"], v[(x["fuente"], x["id_origen"])])
    errores = 0
    for f in focalizacion:
        obtenido = {c for c in (f["causales"] or "").split(";") if c in set(causales_bloqueo)}
        if obtenido != esperado(info[real_de[f["id_persona"]]]):
            errores += 1
    return errores / max(len(focalizacion), 1)


def cobertura_auditoria(userMetadata_commits, ids_bitacora):
    """Fracción de commits Delta de la corrida (userMetadata = id_ejecucion) con fila en la bitácora."""
    commits = [c for c in userMetadata_commits if c]
    if not commits:
        return 0.0
    return sum(1 for c in commits if c in set(ids_bitacora)) / len(commits)
