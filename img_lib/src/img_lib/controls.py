"""Resumen que se presenta al aprobador en cada control humano (Tabla 9, §19).

Los resúmenes son funciones puras sobre listas de dicts; los cuadernos aportan los datos de Delta.
El plazo vencido se trata como rechazo (§19)."""
from collections import Counter

CONTROLS = {  # Tabla 9: control -> (momento, responsable sugerido)
    "C1": ("Sources in Gold (quarantine and counts)", "Data lead"),
    "C2": ("Crosscheck base (match % per source)", "Lead analyst"),
    "C3": ("Settlement (reasons, amounts vs ceiling)", "Transfers functional lead"),
    "C4": ("Payment lists and report", "Program owner"),
}
DECISIONS = {"PENDING", "APPROVED", "REJECTED", "EXPIRED"}


def summary_c1(deliveries, quarantine, gold_by_source):
    return {"control": "C1", "moment": CONTROLS["C1"][0],
            "deliveries": [{k: e[k] for k in ("source", "n_records", "sha256")} for e in deliveries],
            "quarantine_by_cause": dict(Counter(c["cause"] for c in quarantine)),
            "records_in_gold": gold_by_source}


def summary_c2(base, pct):
    return {"control": "C2", "moment": CONTROLS["C2"][0], "universe": len(base),
            "validation_match_pct": round(pct, 2)}


def summary_c3(targeting, payments, source_status, sources):
    ceiling = {f["funding_source"]: float(f["ceiling"]) for f in sources}
    reasons = Counter(c for f in targeting for c in (f["reasons"] or "").split(";") if c)
    return {"control": "C3", "moment": CONTROLS["C3"][0],
            "eligible": sum(1 for f in targeting if f["eligible"]),
            "exclusions_by_reason": dict(reasons),
            "total_amount": sum(p["amount"] for p in payments), "ceiling_by_source": ceiling,
            "payments_over_ceiling": source_status["payments_over_ceiling"]}


def summary_c4(report):
    return {"control": "C4", "moment": CONTROLS["C4"][0], "counts": report["counts"],
            "lists_sum_equals_settlement": report["lists_sum_equals_settlement"],
            "uses_illustrative_params": report["uses_illustrative_params"]}


def approval_row(*, cycle_id, control, decision, approver, mechanism, requested_at, decided_at,
                    comment=None, pipeline_run_id=None):
    if control not in CONTROLS:
        raise ValueError(f"unknown control: {control}")
    if decision not in DECISIONS:
        raise ValueError(f"invalid decision: {decision}")
    return {"cycle_id": cycle_id, "control": control, "responsible_role": CONTROLS[control][1],
            "requested_at": requested_at, "decided_at": decided_at, "decision": decision,
            "approver": approver, "comment": comment, "mechanism": mechanism,
            "pipeline_run_id": pipeline_run_id}


def all_approved(rows, cycle_id, controls=("C1", "C2", "C3", "C4")):
    """Último estado por control: solo APPROVED cuenta. PENDING, EXPIRED o ausente = no aprobado."""
    last = {}
    by_date = sorted((f for f in rows if f["cycle_id"] == cycle_id),
                       key=lambda f: f["decided_at"] or f["requested_at"] or "")
    for f in by_date:
        last[f["control"]] = f["decision"]
    return all(last.get(c) == "APPROVED" for c in controls)
