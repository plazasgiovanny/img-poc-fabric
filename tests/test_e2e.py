"""Cadena lógica completa (Plata -> MDM -> Oro -> cruces -> liquidación -> listados -> informe) sobre
datos sintéticos, sin Spark. Verifica los criterios de la PoC antes de llevarla a Fabric."""
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "img_lib" / "src"))
sys.path.insert(0, str(ROOT / "generator"))

from img_lib.validate import validate_record

import generator
from img_lib import active, crosschecks, mdm, metrics, settlement
from img_lib import illustrative as ill

TODAY = date(2026, 10, 1)
CUTOFF = "2026-09-30"


def run_chain(n=500, cutoff=1):
    data = generator.generate(n, cutoff)
    silver, quarantine = [], []
    for source in ("population", "validation"):
        for r in data[source]:
            rec, causes = validate_record({**r, "source": source}, today=TODAY)
            (quarantine if causes else silver).append(rec)
    people, xref = mdm.build_master(silver)
    _, assign = mdm.build_households(people)
    person_of = {(x["source"], x["origin_id"]): x["person_id"] for x in xref}
    gold = {"population": [], "validation": []}
    for r in silver:
        pid = person_of[(r["source"], r["origin_id"])]
        gold[r["source"]].append({**r, "person_id": pid, "household_id": assign[pid]})
    base = crosschecks.build_base(gold["population"], gold["validation"], cycle_id="2026-09", cutoff_date=CUTOFF,
                                 source_versions={"population": "c1", "validation": "c1"},
                                 execution_id="E-test", notebook_version="test", ts="2026-10-01T00:00:00")
    p = {k: active(getattr(ill, k), CUTOFF) for k in
         ("TARGETING_CRITERIA", "BLOCK_RULES", "HOLDER_RULE", "OPERATORS", "AMOUNTS", "FUNDING_SOURCES")}
    tgt = settlement.target(base, p["TARGETING_CRITERIA"], p["BLOCK_RULES"])
    hld = settlement.select_holder(tgt, base, p["HOLDER_RULE"])
    mp = settlement.assign_payment_method(hld, p["OPERATORS"])
    amt = settlement.calculate_amount(hld, p["AMOUNTS"])
    payments, status = settlement.assign_funding_source(amt, p["FUNDING_SOURCES"])
    master_sheet, files = settlement.generate_payment_lists(payments, mp, base)
    return dict(data=data, quarantine=quarantine, xref=xref, base=base, p=p, tgt=tgt, hld=hld, payments=payments,
                status=status, master_sheet=master_sheet, files=files)


def test_full_chain_and_criteria():
    c = run_chain()
    v = c["data"]["ground_truth"]
    # base de cruces: una fila por persona, con los grupos de la Tabla 7
    ids = [r["person_id"] for r in c["base"]]
    assert len(ids) == len(set(ids))
    for field in ("cycle_id", "person_id", "household_id", "sisben_group", "validation_found", "execution_id"):
        assert field in c["base"][0]
    # un titular por hogar elegible
    eligible_households = {f["household_id"] for f in c["tgt"] if f["eligible"]}
    assert {t["household_id"] for t in c["hld"]} == eligible_households and len(c["hld"]) == len(eligible_households)
    # el titular es elegible
    eligible = {f["person_id"] for f in c["tgt"] if f["eligible"]}
    assert all(t["person_id"] in eligible for t in c["hld"])
    # error de bloqueo < 1 % contra la verdad conocida
    def expected(i):
        s = set()
        if i["deceased"] and i["in_validation"]:
            s.add("DECEASED_IN_VALIDATION")
        if not i["in_validation"]:
            s.add("NOT_FOUND_IN_VALIDATION")
        return s
    reasons = [b["reason"] for b in c["p"]["BLOCK_RULES"]]
    assert metrics.block_error_rate(v, c["xref"], c["tgt"], expected, reasons) < 0.01
    # suma de listados == liquidación
    assert abs(sum(f["amount"] for f in c["master_sheet"]) - sum(p["amount"] for p in c["payments"])) < 1e-6
    assert 0 < crosschecks.match_pct(c["base"]) < 100


def test_report_publication_and_fingerprint(tmp_path):
    c = run_chain()
    inf = settlement.build_report(
        cycle_id="2026-09", cutoff_date=CUTOFF, source_versions={"population": "c1"},
        applied_params=c["p"], notebook_versions={"nb_00": "test"}, base=c["base"],
        targeting=c["tgt"], holders=c["hld"], payments=c["payments"], master_sheet=c["master_sheet"], approvals=[])
    assert inf["uses_illustrative_params"] is True  # R8: debe verse en el informe
    assert inf["lists_sum_equals_settlement"] is True
    assert inf["counts"]["settled_payments"] == len(c["hld"])
    man = settlement.publish(c["files"], str(tmp_path), "2026-09")
    assert man and (tmp_path / "2026-09" / "manifest_sha256.csv").exists()
    from img_lib import sha256_file
    for m in man:
        assert sha256_file(str(tmp_path / "2026-09" / m["file"])) == m["sha256"]
    with open(tmp_path / "2026-09" / man[0]["file"], encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == man[0]["rows"]


def test_audit_coverage():
    assert metrics.audit_coverage(["E1", "E1", "E2"], ["E1", "E2"]) == 1.0
    assert metrics.audit_coverage(["E1", "E3"], ["E1"]) == 0.5


def test_mdm_and_quarantine_error_at_5000():
    c = run_chain(5000)
    v = c["data"]["ground_truth"]
    assert metrics.mdm_error_rate(v, c["xref"]) < 0.01
    ids = {(("population" if r["origin_id"].startswith("POP") else "validation"), r["origin_id"])
           for r in c["quarantine"]}
    assert metrics.quarantine_error_rate(v, ids) < 0.01
