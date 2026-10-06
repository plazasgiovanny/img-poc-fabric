import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pipeline_tool as pt  # noqa: E402

CFG = {
    "workspace_id": "11111111-1111-1111-1111-111111111111",
    "approvers": "aprobador@ejemplo.test",
    "teams_chat_id": "19:abcdef0123456789@thread.v2",
    "teams_connection_id": "22222222-2222-2222-2222-222222222222",
    "notebook_ids": {"nb_env_check_child_a": "33333333-3333-3333-3333-333333333333",
                     "nb_env_check_child_b": "44444444-4444-4444-4444-444444444444"},
}
TEMPLATES = sorted(pt.TEMPLATES.glob("*.template.json"))


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_template_has_no_environment_identifiers(path):
    """Repo público: ni un GUID ni un correo ni un chatId en las plantillas ni en el ejemplo."""
    for p in (path, ROOT / "pipelines" / "local.example.json"):
        text = p.read_text(encoding="utf-8")
        assert not pt.GUID.findall(text) and not pt.EMAIL.findall(text), p.name


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_template_placeholders_are_known_and_graph_is_valid(path):
    text = path.read_text(encoding="utf-8")
    for key, _ in pt.placeholders_in(text):
        assert key in pt.SIMPLE or key == "NOTEBOOK_ID", key
    pt.check_graph(json.loads(pt.PLACEHOLDER.sub("x", text)))


def test_render_resolves_everything_and_keeps_the_graph():
    text = (pt.TEMPLATES / "pl_env_check_approval.template.json").read_text(encoding="utf-8")
    out = json.loads(pt.render(text, CFG))
    assert not pt.PLACEHOLDER.findall(json.dumps(out))
    acts = {a["name"]: a for a in out["properties"]["activities"]}
    assert acts["NotebookA"]["typeProperties"]["notebookId"] == CFG["notebook_ids"]["nb_env_check_child_a"]
    assert acts["Approval1"]["externalReferences"]["connection"] == CFG["teams_connection_id"]


def test_rejected_or_expired_approval_goes_to_fail_not_to_notebook_b():
    """El motivo del diseño: un rechazo o vencimiento hacen fallar a Approval1; la ruta de fallo debe colgar de él."""
    text = (pt.TEMPLATES / "pl_env_check_approval.template.json").read_text(encoding="utf-8")
    acts = {a["name"]: a for a in json.loads(pt.render(text, CFG))["properties"]["activities"]}
    assert acts["Fail"]["dependsOn"] == [{"activity": "Approval1", "dependencyConditions": ["Failed"]}]
    assert acts["NotebookB"]["dependsOn"] == [{"activity": "Approval1", "dependencyConditions": ["Succeeded"]}]
    assert acts["Approval1"]["policy"]["timeout"] == "0.00:10:00"


def test_render_fails_when_a_value_is_missing():
    text = (pt.TEMPLATES / "pl_env_check_approval.template.json").read_text(encoding="utf-8")
    with pytest.raises(KeyError, match="approvers"):
        pt.render(text, {k: v for k, v in CFG.items() if k != "approvers"})


def test_templatize_roundtrip_removes_system_fields_and_ids():
    text = (pt.TEMPLATES / "pl_env_check_approval.template.json").read_text(encoding="utf-8")
    exported = json.loads(pt.render(text, CFG))
    exported["objectId"] = "55555555-5555-5555-5555-555555555555"
    exported["properties"]["lastModifiedByObjectId"] = "66666666-6666-6666-6666-666666666666"
    exported["properties"]["lastPublishTime"] = "2026-10-03T21:42:59Z"
    back = pt.to_template(exported, CFG)
    assert json.loads(back) == json.loads(text)


def test_templatize_refuses_to_leak_unknown_identifiers():
    text = (pt.TEMPLATES / "pl_env_check_approval.template.json").read_text(encoding="utf-8")
    exported = json.loads(pt.render(text, CFG))
    exported["properties"]["activities"][0]["typeProperties"]["workspaceId"] = "77777777-7777-7777-7777-777777777777"
    with pytest.raises(ValueError, match="sin marcador"):
        pt.to_template(exported, CFG)


def test_check_graph_rejects_dangling_dependencies_and_cycles():
    def pipe(deps):
        return {"properties": {"activities": [
            {"name": n, "type": "Fail", "dependsOn": [{"activity": d, "dependencyConditions": ["Succeeded"]} for d in ds]}
            for n, ds in deps.items()]}}
    pt.check_graph(pipe({"a": [], "b": ["a"]}))
    with pytest.raises(ValueError):
        pt.check_graph(pipe({"a": ["zzz"]}))
    with pytest.raises(ValueError):
        pt.check_graph(pipe({"a": ["b"], "b": ["a"]}))


# ---- pl_img_cycle ----
CYCLE_NBS = ["nb_init_cycle", "nb_orch_e1", "nb_orch_e2", "nb_orch_settlement", "nb_orch_payment_lists",
             "nb_ctl_summary", "nb_record_approval", "nb_07_publish"]
CYCLE_CFG = {**CFG, "notebook_ids": {n: f"{i:08d}-0000-0000-0000-000000000000" for i, n in enumerate(CYCLE_NBS, 1)}}
CYCLE_TEMPLATE = (pt.TEMPLATES / "pl_img_cycle.template.json").read_text(encoding="utf-8")


def _cycle():
    return {a["name"]: a for a in json.loads(pt.render(CYCLE_TEMPLATE, CYCLE_CFG))["properties"]["activities"]}


def _notebook_params(py_name):
    """Variables asignadas en la celda «Parámetros» de un cuaderno .py."""
    import re
    text = (ROOT / "notebooks" / f"{py_name}.py").read_text(encoding="utf-8")
    cell = text.split("# %% Parámetros", 1)[1].split("# %%", 1)[0]
    return set(re.findall(r"^([A-Za-z_]\w*)\s*=", cell, re.M))


def test_cycle_render_is_valid_json_and_complete():
    acts = _cycle()
    assert not pt.PLACEHOLDER.findall(json.dumps(acts))
    assert pt.missing_notebooks(CYCLE_TEMPLATE, CYCLE_CFG) == []
    assert set(pt.missing_notebooks(CYCLE_TEMPLATE, CFG)) == set(CYCLE_NBS)


def test_cycle_order_follows_design():
    acts = _cycle()
    chain = ["init", "orch_e1", "ctl_c1_summary", "approval_c1", "record_c1", "orch_e2", "ctl_c2_summary",
             "approval_c2", "record_c2", "orch_settlement", "ctl_c3_summary", "approval_c3", "record_c3",
             "orch_payment_lists", "ctl_c4_summary", "approval_c4", "record_c4", "publish"]
    for prev, cur in zip(chain, chain[1:], strict=False):
        assert acts[cur]["dependsOn"] == [{"activity": prev, "dependencyConditions": ["Succeeded"]}], cur
    assert acts["init"]["dependsOn"] == []
    assert "report_final" not in acts      # nb_06_report corre dentro de DAG_PAYMENT_LISTS


def test_cycle_report_is_inside_payment_lists_dag():
    from img_lib.dag import DAG_PAYMENT_LISTS
    assert "nb_06_report" in DAG_PAYMENT_LISTS


def test_cycle_each_approval_has_failed_route_and_30_min_timeout():
    acts = _cycle()
    for c in "1234":
        ap = acts[f"approval_c{c}"]
        assert ap["type"] == "Approval" and ap["policy"]["timeout"] == "0.00:30:00"
        assert acts[f"reject_c{c}"]["dependsOn"] == [{"activity": ap["name"], "dependencyConditions": ["Failed"]}]
        assert acts[f"fail_c{c}"]["dependsOn"][0]["activity"] == f"reject_c{c}"
        assert "ActionTimedOut" in acts[f"reject_c{c}"]["typeProperties"]["parameters"]["decision"]["value"]["value"]
        assert acts[f"record_c{c}"]["typeProperties"]["parameters"]["decided_at"]["value"]["value"] == "@utcNow()"


def test_cycle_parameters_exist_in_notebook_parameter_cells():
    inv = {v: k for k, v in CYCLE_CFG["notebook_ids"].items()}
    for name, a in _cycle().items():
        if a["type"] != "TridentNotebook":
            continue
        nb = inv[a["typeProperties"]["notebookId"]]
        passed = set(a["typeProperties"]["parameters"])
        assert passed <= _notebook_params(nb), (name, passed - _notebook_params(nb))
        assert "NOTEBOOK_VERSION" not in passed


def test_cycle_pipeline_parameters_are_declared():
    p = json.loads(pt.render(CYCLE_TEMPLATE, CYCLE_CFG))["properties"]["parameters"]
    assert set(p) == {"cycle_id", "cutoff", "cutoff_date"}


def test_parse_ids_text_ignores_noise():
    got = pt.parse_ids_text("nb_a 33333333-3333-3333-3333-333333333333\nruido\nnb_b  44444444-4444-4444-4444-444444444444\n")
    assert got == {"nb_a": "33333333-3333-3333-3333-333333333333", "nb_b": "44444444-4444-4444-4444-444444444444"}
