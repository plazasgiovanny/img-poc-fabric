"""Métricas del Experimento 2 (§7): errores <1 %, auditoría 100 %.

La comparación es contra la VERDAD CONOCIDA del generador sintético, no contra el manual."""


def quarantine_error_rate(ground_truth, quarantine_ids):
    """ground_truth: filas con source, origin_id, goes_to_quarantine. quarantine_ids: {(source, origin_id)}."""
    expected = {(v["source"], v["origin_id"]) for v in ground_truth if int(v["goes_to_quarantine"])}
    return len(expected ^ set(quarantine_ids)) / max(len(ground_truth), 1)


def mdm_error_rate(ground_truth, xref):
    """Personas distintas unidas (falso positivo) + una persona partida (falso negativo), sobre
    el total de personas reales."""
    v = {(x["source"], x["origin_id"]): x["true_person_id"] for x in ground_truth}
    by_master, by_true = {}, {}
    for x in xref:
        real = v[(x["source"], x["origin_id"])]
        by_master.setdefault(x["person_id"], set()).add(real)
        by_true.setdefault(real, set()).add(x["person_id"])
    errors = sum(len(s) > 1 for s in by_master.values()) + sum(len(s) > 1 for s in by_true.values())
    return errors / max(len(by_true), 1)


def _true_of(ground_truth, xref):
    v = {(x["source"], x["origin_id"]): x["true_person_id"] for x in ground_truth}
    true_of = {}
    for x in xref:
        true_of.setdefault(x["person_id"], v[(x["source"], x["origin_id"])])
    return true_of


def block_error_rate(ground_truth, xref, targeting, expected, block_reasons):
    """Compara las causales de bloqueo aplicadas con las esperadas según la verdad conocida.

    `expected(info) -> set de reasons`, con info = {"renec_blocked": bool, "in_registry": bool} de la
    persona real (vigencia RENEC bloqueante; existe en inhumados con el mismo tipo y número). Solo cuentan
    las causales de `block_reasons` (las reglas vigentes), así no se mezclan con las de focalización.
    Tasa = filas con causales distintas / filas evaluadas."""
    info = {}
    for x in ground_truth:
        r = info.setdefault(x["true_person_id"], {"renec_blocked": False, "in_registry": False})
        r["renec_blocked"] |= bool(int(x.get("true_renec_blocked", 0)))
        r["in_registry"] |= x["source"] == "validation"
    true_of = _true_of(ground_truth, xref)
    errors = 0
    for f in targeting:
        obtained = {c for c in (f["reasons"] or "").split(";") if c in set(block_reasons)}
        if obtained != expected(info[true_of[f["person_id"]]]):
            errors += 1
    return errors / max(len(targeting), 1)


def holder_error_rate(ground_truth, xref, holders):
    """Titulares obtenidos vs. titulares esperados por la verdad conocida (true_is_holder), sobre el total
    de personas reales de la fuente poblacional."""
    true_of = _true_of(ground_truth, xref)
    expected = {x["true_person_id"] for x in ground_truth if x["source"] == "population" and int(x["true_is_holder"])}
    obtained = {true_of[h["person_id"]] for h in holders}
    people = {x["true_person_id"] for x in ground_truth if x["source"] == "population"}
    return len(expected ^ obtained) / max(len(people), 1)


def audit_coverage(userMetadata_commits, run_log_ids):
    """Fracción de commits Delta de la corrida (userMetadata = execution_id) con fila en la bitácora."""
    commits = [c for c in userMetadata_commits if c]
    if not commits:
        return 0.0
    return sum(1 for c in commits if c in set(run_log_ids)) / len(commits)
