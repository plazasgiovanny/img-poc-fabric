from test_e2e import run_chain

from img_lib import measure


def _log(nb, stage, s, e, n=10, ex="2026-09-a"):
    return {"notebook": nb, "process_stage": stage, "trace_event": "end", "execution_id": ex,
            "start_time": f"2026-10-01T10:00:{s:02d}+00:00", "end_time": f"2026-10-01T10:00:{e:02d}+00:00",
            "records_processed": n}


def test_timings_by_stage_and_chain():
    t = measure.timings([_log("a", "bronze", 0, 5), _log("b", "silver", 5, 15, ex="x2"), _log("c", "control", 15, 59)])
    assert t["by_stage"]["bronze"]["seconds"] == 5 and t["by_stage"]["silver"]["records_processed"] == 10
    assert t["chain_seconds"] == 15  # el control (espera humana) no cuenta


def test_human_approval_pending_to_approved():
    ap = [{"control": "C1", "decision": "PENDING", "requested_at": "2026-10-01T10:00:00+00:00", "decided_at": None},
          {"control": "C1", "decision": "APPROVED", "requested_at": "2026-10-01T10:05:00+00:00",
           "decided_at": "2026-10-01T10:05:00+00:00", "approver": "x"},
          {"control": "C2", "decision": "APPROVED", "requested_at": "2026-10-01T10:05:00+00:00",
           "decided_at": "2026-10-01T10:05:00+00:00"}]
    h = measure.human_approval(ap)
    assert h["by_control"]["C1"]["seconds"] == 300 and h["by_control"]["C2"]["seconds"] is None


def test_traceability_window():
    log = [_log("a", "bronze", 0, 10, ex="E1")]
    commits = [{"table": "t", "version": 0, "timestamp": "2026-10-01 10:00:05", "userMetadata": "E1"},
               {"table": "t", "version": 1, "timestamp": "2026-10-01T10:00:06+00:00", "userMetadata": None},
               {"table": "t", "version": 2, "timestamp": "2026-10-02T00:00:00", "userMetadata": None}]  # fuera de ventana
    tr = measure.traceability(commits, log)
    assert tr["commits_in_cycle_window"] == 2 and tr["audit_coverage"] == 0.5 and tr["notebook_executions"] == 1


def test_funnel_and_quality_on_synthetic_chain():
    c = run_chain()
    gt = [{k: str(v) for k, v in g.items()} for g in c["data"]["ground_truth"]]  # como llega del CSV en Fabric
    q_ids = [(r["source"], r["origin_id"]) for r in c["quarantine"]]
    block = [b["reason"] for b in c["p"]["BLOCK_RULES"]]
    q = measure.quality(gt, c["xref"], c["tgt"], c["hld"], q_ids, block)
    assert all(q[k] < 0.01 for k in ("holder_error", "block_error", "mdm_error", "quarantine_error")), q
    quarantine = [{"cause": "X"}] * len(q_ids)
    f = measure.funnel(deliveries=[{"source": "population", "n_records": 500}], silver_by_source={"population": 400},
                       quarantine=quarantine, universe=len(c["base"]), targeting=c["tgt"], holders=c["hld"],
                       payments=c["payments"])
    assert f["holders"] == len(c["hld"]) and f["total_amount"] == 120000.0 * len(c["payments"])
    assert f["eligible"] == sum(1 for t in c["tgt"] if t["eligible"])


def test_quality_reports_error_instead_of_failing():
    q = measure.quality([{"x": 1}], [], [], [], [], [])
    assert "error" in q["holder_error"]
