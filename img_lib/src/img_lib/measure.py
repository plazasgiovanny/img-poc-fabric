"""Medición del Experimento 2 (§7) para un ciclo: tiempos, embudo, calidad contra la verdad conocida,
trazabilidad y tiempo humano de aprobación. Funciones puras sobre listas de dicts; el cuaderno
`nb_measure` aporta los datos de Delta y escribe el JSON."""
from collections import Counter, defaultdict
from datetime import datetime, timezone

from . import metrics

STAGES = ("bronze", "silver", "mdm", "gold", "crosschecks", "settlement", "payment_lists", "report")
CHAIN_EXCLUDED = ("control", "start")  # las esperas humanas y la apertura del ciclo no son cómputo de la cadena


def parse_ts(s):
    """ISO 8601 (str, datetime o None) a datetime con zona (UTC si viene sin zona)."""
    if s in (None, ""):
        return None
    d = s if isinstance(s, datetime) else datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _seconds(a, b):
    a, b = parse_ts(a), parse_ts(b)
    return None if a is None or b is None else (b - a).total_seconds()


def timings(run_log):
    """Duración de cada ejecución (fin - inicio) por cuaderno y por etapa. Solo filas trace_event = 'end'."""
    rows = [r for r in run_log if r.get("trace_event") == "end"]
    notebooks = []
    stages = defaultdict(lambda: {"seconds": 0.0, "records_processed": 0, "executions": 0})
    for r in sorted(rows, key=lambda r: str(r.get("start_time"))):
        d = _seconds(r.get("start_time"), r.get("end_time"))
        notebooks.append({"notebook": r["notebook"], "stage": r["process_stage"], "seconds": d,
                          "records_processed": r.get("records_processed"), "execution_id": r["execution_id"]})
        s = stages[r["process_stage"]]
        s["seconds"] += d or 0.0
        s["records_processed"] += int(r.get("records_processed") or 0)
        s["executions"] += 1
    chain = sum(v["seconds"] for k, v in stages.items() if k not in CHAIN_EXCLUDED)
    return {"by_notebook": notebooks,
            "by_stage": {k: {**v, "seconds": round(v["seconds"], 3)} for k, v in stages.items()},
            "chain_seconds": round(chain, 3),
            "note": "chain = suma de duraciones de cuaderno (sin 'control' ni 'start'); "
                    "no incluye esperas entre actividades del pipeline"}


def human_approval(approvals):
    """Por control: decided_at(APPROVED) - requested_at del PENDING más reciente anterior. Sin PENDING, sin tiempo."""
    out, total = {}, 0.0
    for c in sorted({a["control"] for a in approvals}):
        rows = sorted((a for a in approvals if a["control"] == c),
                      key=lambda a: str(a.get("decided_at") or a.get("requested_at")))
        pend = [parse_ts(a["requested_at"]) for a in rows if a["decision"] == "PENDING"]
        appr = [a for a in rows if a["decision"] == "APPROVED" and a.get("decided_at")]
        if not appr:
            out[c] = {"seconds": None, "note": "sin aprobación"}
            continue
        t_dec = parse_ts(appr[-1]["decided_at"])
        before = [p for p in pend if p and p <= t_dec]
        if not before:
            out[c] = {"seconds": None, "note": "sin solicitud PENDING previa", "approver": appr[-1].get("approver")}
            continue
        sec = round((t_dec - max(before)).total_seconds(), 3)
        out[c] = {"seconds": sec, "approver": appr[-1].get("approver")}
        total += sec
    return {"by_control": out, "total_seconds": round(total, 3),
            "note": "tiempo humano separado del cómputo; con nb_approve (demo) la espera es ~0"}


def funnel(*, deliveries, silver_by_source, quarantine, universe, targeting, holders, payments):
    """Bronce -> Plata -> cuarentena -> universo -> elegibles -> titulares -> pagos. Las exclusiones cuentan
    MOTIVOS (una persona con dos motivos cuenta dos veces), no personas."""
    bronze = {d["source"]: int(d["n_records"]) for d in deliveries}
    reasons = Counter(c for f in targeting for c in (f["reasons"] or "").split(";") if c)
    return {
        "bronze_by_source": bronze, "bronze_total": sum(bronze.values()),
        "silver_by_source": silver_by_source, "silver_total": sum(silver_by_source.values()),
        "quarantine_total": len(quarantine),
        "quarantine_by_cause": dict(Counter(q["cause"] for q in quarantine)),
        "exact_duplicates_removed": sum(bronze.values()) - sum(silver_by_source.values()) - len(quarantine),
        "universe": universe, "eligible": sum(1 for f in targeting if f["eligible"]),
        "holders": len(holders), "payments": len(payments),
        "total_amount": sum(float(p["amount"]) for p in payments),
        "exclusions_by_reason": dict(reasons),
        "note": "exclusions_by_reason cuenta motivos, no personas",
    }


def expected_block_reasons(info):
    s = set()
    if info["renec_blocked"]:
        s.add("RENEC_NOT_VALID")
    if info["in_registry"]:
        s.add("IN_DECEASED_REGISTRY")
    return s


def _safe(fn):
    try:
        return round(fn(), 6)
    except Exception as e:  # noqa: BLE001 - la medición no debe tumbarse por un formato inesperado
        return {"error": f"{type(e).__name__}: {e}"}


def quality(ground_truth, xref, targeting, holders, quarantine_ids, block_reasons):
    """Las mismas métricas de tests/test_e2e.py. ground_truth = filas del CSV del generador (todo str)."""
    q = {(str(s), str(o)) for s, o in quarantine_ids}
    gt = [{**g, "origin_id": str(g.get("origin_id"))} for g in ground_truth]
    xr = [{**x, "origin_id": str(x.get("origin_id"))} for x in xref]
    return {
        "holder_error": _safe(lambda: metrics.holder_error_rate(gt, xr, holders)),
        "block_error": _safe(lambda: metrics.block_error_rate(gt, xr, targeting, expected_block_reasons, block_reasons)),
        "mdm_error": _safe(lambda: metrics.mdm_error_rate(gt, xr)),
        "quarantine_error": _safe(lambda: metrics.quarantine_error_rate(gt, q)),
        "ground_truth_rows": len(gt), "threshold": 0.01,
    }


def traceability(commits, run_log):
    """commits: [{table, version, timestamp, userMetadata}] de DESCRIBE HISTORY. Se cuentan los commits dentro de
    la ventana del ciclo (primer inicio - último fin de la bitácora); cubierto = su userMetadata está en la bitácora."""
    ids = {r["execution_id"] for r in run_log if r.get("execution_id")}
    ts = [t for r in run_log for t in (parse_ts(r.get("start_time")), parse_ts(r.get("end_time"))) if t]
    lo, hi = (min(ts), max(ts)) if ts else (None, None)
    inside = []
    for c in commits:
        t = parse_ts(c["timestamp"])
        if lo and t and lo <= t <= hi:
            inside.append(c)
    covered = sum(1 for c in inside if c.get("userMetadata") in ids)
    return {"notebook_executions": len({r["execution_id"] for r in run_log if r.get("trace_event") == "end"}),
            "run_log_rows": len(run_log), "commits_in_cycle_window": len(inside),
            "commits_with_execution_id": covered,
            "audit_coverage": round(covered / len(inside), 4) if inside else None,
            "audit_coverage_check": metrics.audit_coverage([c.get("userMetadata") for c in inside], ids) if inside else None,
            "note": "commits sin userMetadata dentro de la ventana bajan la cobertura (p. ej. escritura manual)"}


def _fmt(v):
    return f"{v:.2f} s" if isinstance(v, (int, float)) else str(v)


def render(m):
    """Texto legible con tablas pequeñas."""
    lines = [f"== Medición del ciclo {m['cycle_id']} (corte {m.get('cutoff')}) ==", "", "-- Tiempos por etapa --"]
    for k, v in m["timings"]["by_stage"].items():
        lines.append(f"  {k:<14}{_fmt(v['seconds']):>12}  registros={v['records_processed']}  ejecuciones={v['executions']}")
    lines.append(f"  cadena automática: {_fmt(m['timings']['chain_seconds'])}")
    f = m["funnel"]
    lines += ["", "-- Embudo --"]
    for k in ("bronze_total", "silver_total", "quarantine_total", "exact_duplicates_removed", "universe", "eligible",
              "holders", "payments", "total_amount"):
        lines.append(f"  {k:<26}{f[k]}")
    lines.append(f"  cuarentena por causa: {f['quarantine_by_cause']}")
    lines.append(f"  exclusiones por motivo (motivos, no personas): {f['exclusions_by_reason']}")
    lines += ["", "-- Calidad vs verdad conocida (umbral < 1 %) --"]
    if "error" in m["quality"]:
        lines.append(f"  {m['quality']['error']}")
    for k in ("holder_error", "block_error", "mdm_error", "quarantine_error"):
        v = m["quality"].get(k)
        if v is not None:
            lines.append(f"  {k:<18}{v:.4%}" if isinstance(v, float) else f"  {k:<18}{v}")
    t = m["traceability"]
    lines += ["", "-- Trazabilidad --",
              f"  ejecuciones de cuadernos={t['notebook_executions']}  commits en ventana={t['commits_in_cycle_window']}"
              f"  con execution_id={t['commits_with_execution_id']}  cobertura={t['audit_coverage']}"]
    h = m["human_approval"]
    lines += ["", "-- Aprobación humana --"] + [f"  {c}: {_fmt(v['seconds'])}" for c, v in h["by_control"].items()]
    lines.append(f"  total: {_fmt(h['total_seconds'])}")
    return "\n".join(lines)
