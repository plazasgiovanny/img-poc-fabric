import sys
import types
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


# ---- escritura Delta con Spark simulado: cubre cycle.write y run_log.record sin necesitar Fabric ----
class _FakeWriter:
    def __init__(self, sink):
        self.sink = sink

    def format(self, f):
        self.sink["format"] = f
        return self

    def mode(self, m):
        self.sink["mode"] = m
        return self

    def saveAsTable(self, t):  # noqa: N802 - API de Spark
        self.sink["table"] = t


class _FakeDF:
    def __init__(self, sink, rows, schema):
        sink["rows"], sink["schema"] = rows, schema
        self.write = _FakeWriter(sink)


class _FakeSpark:
    def __init__(self, existing=None):
        self.sink, self.existing = {}, existing or {}
        self.catalog = types.SimpleNamespace(tableExists=lambda t: t in self.existing)

    def table(self, t):
        return types.SimpleNamespace(schema=self.existing[t])

    def createDataFrame(self, rows, schema=None):  # noqa: N802 - API de Spark
        return _FakeDF(self.sink, rows, schema)


def test_write_infers_schema_when_table_is_missing():
    from img_lib.cycle import ddl_types, write
    spark, rows = _FakeSpark(), [{"a": None, "b": 1}]
    assert write(spark, rows, "lh_x.s.t") == 1
    assert spark.sink["schema"] == ddl_types(rows) and spark.sink["table"] == "lh_x.s.t" and spark.sink["mode"] == "append"


def test_write_uses_the_existing_table_schema():
    """Una columna todo None conserva el tipo declarado de la tabla (p. ej. BIGINT), no cae a string."""
    from img_lib.cycle import write
    esquema = types.SimpleNamespace(names=["a", "b"])
    spark = _FakeSpark({"lh_x.s.t": esquema})
    write(spark, [{"a": None, "b": 1}], "lh_x.s.t")
    assert spark.sink["schema"] is esquema


def test_write_ignores_empty_rows():
    from img_lib.cycle import write
    spark = _FakeSpark()
    assert write(spark, [], "lh_x.s.t") == 0 and spark.sink == {}


def test_run_log_record_writes_none_columns_with_the_table_schema():
    from img_lib import run_log
    esquema = types.SimpleNamespace(names=list(run_log.event(cycle_id="c", execution_id="e", notebook="n",
                                                              notebook_version="v", process_stage="s", trace_event="t")))
    spark = _FakeSpark({run_log.RUN_LOG_TABLE: esquema})
    row = run_log.event(cycle_id="c", execution_id="e", notebook="n", notebook_version="v",
                        process_stage="s", trace_event="t")
    assert row["data_source"] is None and row["notes"] is None      # el caso que antes rompía la inferencia de esquema
    run_log.record(spark, row)
    assert spark.sink["table"] == run_log.RUN_LOG_TABLE and spark.sink["schema"] is esquema and spark.sink["rows"] == [row]


def test_run_log_record_accepts_another_table():
    from img_lib import run_log
    spark = _FakeSpark()
    run_log.record(spark, {"x": 1}, "lh_control.ctl.env_check_run_log")
    assert spark.sink["table"] == "lh_control.ctl.env_check_run_log"


def test_write_rejects_columns_missing_in_existing_table():
    from img_lib.cycle import extra_columns, write
    assert extra_columns([{"a": 1, "b": 2}, {"a": 1, "c": 3}], ["a", "b"]) == ["c"]
    spark = _FakeSpark({"lh_x.s.t": types.SimpleNamespace(names=["a", "b"])})
    with pytest.raises(ValueError, match="columns not in table lh_x.s.t: c"):
        write(spark, [{"a": 1, "c": 2}], "lh_x.s.t")
    assert spark.sink == {}
