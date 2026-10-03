import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "img_lib" / "src"))
sys.path.insert(0, str(ROOT / "generator"))

from img_lib.params import has_illustrative
from img_lib.validate import validate_keys, validate_record

import generator
from img_lib import (
    active,
    mdm,
    normalize_doc_number,
    normalize_name,
    run_log,
    sha256_bytes,
)

TODAY = date(2026, 10, 1)


def test_normalize_doc_number():
    assert normalize_doc_number("99.123.456") == ("99123456", None)
    assert normalize_doc_number("99A123456")[1] == "document_not_numeric"
    assert normalize_doc_number("123")[1] == "document_invalid_length"
    assert normalize_doc_number("")[1] == "document_empty"


def test_normalize_name():
    assert normalize_name("  José  Muñoz ") == ("JOSE MUÑOZ", None)
    assert normalize_name(None)[1] == "name_empty"


def test_fingerprint_stable():
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_active_params():
    rows = [
        {"k": "a", "valid_from": "2026-01-01", "valid_to": None, "is_illustrative": 1},
        {"k": "b", "valid_from": "2025-01-01", "valid_to": "2025-12-31"},
        {"k": "c", "valid_from": "2026-12-01", "valid_to": None},
    ]
    v = active(rows, "2026-09-30")
    assert [f["k"] for f in v] == ["a"] and has_illustrative(v)


def test_validate_keys():
    assert validate_keys([{"a": 1}, {"a": 1}, {"a": None}], ["a"])


def test_run_log_fields():
    e = run_log.event(cycle_id="2026-09", execution_id="E1", notebook="nb", notebook_version="v",
                        process_stage="bronze", trace_event="end")
    assert all(c in e for c in run_log.INSTRUMENT_A_FIELDS + run_log.TRACEABILITY_FIELDS)
    assert e["batch_id"] == "E1"


def test_generator_deterministic_and_defects():
    a = generator.generate(500, 1)
    b = generator.generate(500, 1)
    assert a == b
    defects = "|".join(v["defects"] for v in a["ground_truth"])
    for d in ("malformed_doc", "exact_duplicate", "name_variant"):
        assert d in defects
    assert all(r["doc_number"].startswith("99") for r in a["population"] if r["doc_number"][:2].isdigit())


def test_logical_pipeline_against_ground_truth():
    """Plata + MDM contra la verdad conocida: error < 1 % en cuarentena y en unificación de personas."""
    data = generator.generate(500, 1)
    ground_truth = {(v["source"], v["origin_id"]): v for v in data["ground_truth"]}
    silver, quarantine = [], []
    for source in ("population", "validation"):
        for r in data[source]:
            rec, causes = validate_record({**r, "source": source}, today=TODAY)
            (quarantine if causes else silver).append(rec)

    # cuarentena: exactamente lo que la verdad dice
    expected = {k for k, v in ground_truth.items() if v["goes_to_quarantine"]}
    obtained = {(("population" if r["origin_id"].startswith("POP") else "validation"), r["origin_id"])
                 for r in quarantine}
    q_errors = len(expected ^ obtained)
    assert q_errors / len(ground_truth) < 0.01

    _, xref = mdm.build_master(silver)
    by_id = {}
    for x in xref:
        by_id.setdefault(x["person_id"], set()).add(ground_truth[(x["source"], x["origin_id"])]["true_person_id"])
    merges = sum(1 for s in by_id.values() if len(s) > 1)  # personas distintas unidas (falso positivo)
    true_to_ids = {}
    for x in xref:
        true_to_ids.setdefault(ground_truth[(x["source"], x["origin_id"])]["true_person_id"], set()).add(x["person_id"])
    splits = sum(1 for s in true_to_ids.values() if len(s) > 1)  # una persona partida (falso negativo)
    assert (merges + splits) / len(true_to_ids) < 0.01


def test_cutoff2_changes_few():
    c1, c2 = generator.generate(500, 1), generator.generate(500, 2)
    st1 = {v["true_person_id"]: v["true_status"] for v in c1["ground_truth"]}
    st2 = {v["true_person_id"]: v["true_status"] for v in c2["ground_truth"]}
    changes = sum(1 for k in st1 if k in st2 and st1[k] != st2[k])
    assert 0 < changes < 0.05 * len(st1)
