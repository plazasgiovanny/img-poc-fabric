import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "img_lib" / "src"))

from img_lib import controles, dag


def test_dag_valido_y_args():
    d = dag.construir_dag(dag.DAG_LIQ, "2026-09", "run-1")
    por_nombre = {a["name"]: a for a in d["activities"]}
    assert set(por_nombre["nb_02_medio_pago"]["dependencies"]) == {"nb_01_titular"}
    assert por_nombre["nb_04_fuente_recursos"]["dependencies"] == ["nb_03_monto"]  # requiere el monto
    assert por_nombre["nb_00_focalizacion"]["args"] == {"id_ciclo": "2026-09", "pipeline_run_id": "run-1"}
    assert d["activities"][0]["timeoutPerCellInSeconds"] > 90  # el valor por defecto de runMultiple


@pytest.mark.parametrize("grafo", [dag.DAG_E1, dag.DAG_E2, dag.DAG_LISTADOS])
def test_dags_del_pipeline_son_validos(grafo):
    dag.construir_dag(grafo, "2026-09")


def test_dag_rechaza_ciclos_y_dependencias_fantasma():
    with pytest.raises(ValueError):
        dag.validar({"a": ["b"], "b": ["a"]})
    with pytest.raises(ValueError):
        dag.validar({"a": ["x"]})


def _fila(control, decision, t):
    return controles.fila_aprobacion(id_ciclo="2026-09", control=control, decision=decision, aprobador="u",
                                     mecanismo="tabla", solicitado_en="t0", decidido_en=t)


def test_vencido_o_ausente_no_aprueba():
    ok = [_fila(c, "APROBADO", f"t{i}") for i, c in enumerate(("C1", "C2", "C3", "C4"))]
    assert controles.todas_aprobadas(ok, "2026-09")
    assert not controles.todas_aprobadas(ok[:3], "2026-09")  # falta C4
    assert not controles.todas_aprobadas(ok + [_fila("C2", "VENCIDO", "t9")], "2026-09")  # último estado manda


def test_fila_aprobacion_valida_entradas():
    with pytest.raises(ValueError):
        controles.fila_aprobacion(id_ciclo="x", control="C9", decision="APROBADO", aprobador="u",
                                  mecanismo="m", solicitado_en="a", decidido_en="b")
    with pytest.raises(ValueError):
        _fila("C1", "TAL_VEZ", "t")


def test_ddl_tipos_columnas_todo_none_son_string():
    from datetime import date

    from img_lib.ciclo import ddl_tipos

    filas = [{"a": None, "b": 1, "c": 1.5, "d": date(2026, 9, 30), "e": "x", "f": True},
             {"a": None, "b": 2, "c": 2, "d": date(2026, 10, 1), "e": None, "f": False}]
    assert ddl_tipos(filas) == "`a` string, `b` bigint, `c` double, `d` date, `e` string, `f` boolean"


def test_solicitud_pendiente_no_aprueba_y_reabre():
    base = [_fila(c, "APROBADO", f"t{i}") for i, c in enumerate(("C1", "C2", "C3", "C4"))]
    assert controles.todas_aprobadas(base, "2026-09")
    nueva = controles.fila_aprobacion(id_ciclo="2026-09", control="C3", decision="PENDIENTE", aprobador=None,
                                      mecanismo="solicitud", solicitado_en="t99", decidido_en=None)
    assert not controles.todas_aprobadas(base + [nueva], "2026-09")  # una nueva solicitud reabre el control
