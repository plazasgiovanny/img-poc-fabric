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
