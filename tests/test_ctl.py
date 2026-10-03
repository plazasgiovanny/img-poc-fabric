import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "img_lib" / "src"))

from img_lib import controls, dag


def test_dag_valid_and_args():
    d = dag.build_dag(dag.DAG_SETTLEMENT, "2026-09", "run-1")
    by_name = {a["name"]: a for a in d["activities"]}
    assert set(by_name["nb_02_payment_method"]["dependencies"]) == {"nb_01_holder"}
    assert by_name["nb_04_funding_source"]["dependencies"] == ["nb_03_amount"]  # requiere el monto
    assert by_name["nb_00_targeting"]["args"] == {"cycle_id": "2026-09", "pipeline_run_id": "run-1"}
    assert d["activities"][0]["timeoutPerCellInSeconds"] > 90  # el valor por defecto de runMultiple


@pytest.mark.parametrize("graph", [dag.DAG_E1, dag.DAG_E2, dag.DAG_PAYMENT_LISTS])
def test_pipeline_dags_are_valid(graph):
    dag.build_dag(graph, "2026-09")


def test_dag_rejects_cycles_and_ghost_dependencies():
    with pytest.raises(ValueError):
        dag.validate({"a": ["b"], "b": ["a"]})
    with pytest.raises(ValueError):
        dag.validate({"a": ["x"]})


def _row(control, decision, t):
    return controls.approval_row(cycle_id="2026-09", control=control, decision=decision, approver="u",
                                     mechanism="table", requested_at="t0", decided_at=t)


def test_expired_or_missing_does_not_approve():
    ok = [_row(c, "APPROVED", f"t{i}") for i, c in enumerate(("C1", "C2", "C3", "C4"))]
    assert controls.all_approved(ok, "2026-09")
    assert not controls.all_approved(ok[:3], "2026-09")  # falta C4
    assert not controls.all_approved(ok + [_row("C2", "EXPIRED", "t9")], "2026-09")  # último estado manda


def test_approval_row_validates_inputs():
    with pytest.raises(ValueError):
        controls.approval_row(cycle_id="x", control="C9", decision="APPROVED", approver="u",
                                  mechanism="m", requested_at="a", decided_at="b")
    with pytest.raises(ValueError):
        _row("C1", "MAYBE", "t")


def test_ddl_types_all_none_columns_are_string():
    from datetime import date

    from img_lib.cycle import ddl_types

    rows = [{"a": None, "b": 1, "c": 1.5, "d": date(2026, 9, 30), "e": "x", "f": True},
             {"a": None, "b": 2, "c": 2, "d": date(2026, 10, 1), "e": None, "f": False}]
    assert ddl_types(rows) == "`a` string, `b` bigint, `c` double, `d` date, `e` string, `f` boolean"


def test_pending_request_does_not_approve_and_reopens():
    base = [_row(c, "APPROVED", f"t{i}") for i, c in enumerate(("C1", "C2", "C3", "C4"))]
    assert controls.all_approved(base, "2026-09")
    new = controls.approval_row(cycle_id="2026-09", control="C3", decision="PENDING", approver=None,
                                      mechanism="request", requested_at="t99", decided_at=None)
    assert not controls.all_approved(base + [new], "2026-09")  # una nueva solicitud reabre el control
