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


def block_error_rate(ground_truth, xref, targeting, expected, block_reasons):
    """Compara las causales de bloqueo aplicadas con las esperadas según la verdad conocida.

    `expected(info) -> set de reasons`, con info = {"deceased": bool, "in_validation": bool}
    de la persona real. Solo cuentan las causales de `block_reasons` (las reglas vigentes), así
    no se mezclan con las de focalización. Tasa = filas con causales distintas / filas evaluadas."""
    info = {}
    for x in ground_truth:
        r = info.setdefault(x["true_person_id"], {"deceased": False, "in_validation": False})
        r["deceased"] |= x["true_status"] == "DECEASED"
        r["in_validation"] |= x["source"] == "validation"
    true_of = {}
    v = {(x["source"], x["origin_id"]): x["true_person_id"] for x in ground_truth}
    for x in xref:
        true_of.setdefault(x["person_id"], v[(x["source"], x["origin_id"])])
    errors = 0
    for f in targeting:
        obtained = {c for c in (f["reasons"] or "").split(";") if c in set(block_reasons)}
        if obtained != expected(info[true_of[f["person_id"]]]):
            errors += 1
    return errors / max(len(targeting), 1)


def audit_coverage(userMetadata_commits, run_log_ids):
    """Fracción de commits Delta de la corrida (userMetadata = execution_id) con fila en la bitácora."""
    commits = [c for c in userMetadata_commits if c]
    if not commits:
        return 0.0
    return sum(1 for c in commits if c in set(run_log_ids)) / len(commits)
