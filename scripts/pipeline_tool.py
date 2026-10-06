"""Plantillas de pipelines de Fabric sin identificadores de tu entorno (el repo es público).

Los IDs de workspace, cuadernos, conexiones y chats, y los correos, viven en `pipelines/local.json`
(ignorado por git). Las plantillas de `pipelines/templates/` solo llevan marcadores:

    {{WORKSPACE_ID}}  {{APPROVERS}}  {{TEAMS_CHAT_ID}}  {{TEAMS_CONNECTION_ID}}  {{NOTEBOOK_ID:<nombre del cuaderno>}}

Uso:
    python scripts/pipeline_tool.py list
    python scripts/pipeline_tool.py render pl_env_check_approval          # -> output/pipelines/<nombre>.json
    python scripts/pipeline_tool.py templatize exportado.json            # JSON del portal -> plantilla sin IDs
    python scripts/pipeline_tool.py ids-from-text ids.txt                # líneas "nombre id" -> notebook_ids de local.json
"""
import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "img_lib" / "src"))
from img_lib.dag import validate as validate_dag  # noqa: E402

TEMPLATES = REPO / "pipelines" / "templates"
LOCAL = REPO / "pipelines" / "local.json"
OUTPUT = REPO / "output" / "pipelines"

SYSTEM_FIELDS = ("objectId", "lastModifiedByObjectId", "lastPublishTime")   # los asigna Fabric
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)(?::([A-Za-z0-9_]+))?\}\}")
GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")        # también atrapa chatId tipo "19:xxxx@thread.v2"
CONDITIONS = {"Succeeded", "Failed", "Skipped", "Completed"}
SIMPLE = {"WORKSPACE_ID": "workspace_id", "APPROVERS": "approvers", "TEAMS_CHAT_ID": "teams_chat_id",
          "TEAMS_CONNECTION_ID": "teams_connection_id"}


def placeholders_in(text: str) -> set:
    """Marcadores presentes en un texto, como tuplas (clave, argumento|None)."""
    return {(m.group(1), m.group(2)) for m in PLACEHOLDER.finditer(text)}


def resolve(key: str, arg, cfg: dict) -> str:
    if key == "NOTEBOOK_ID":
        try:
            return cfg["notebook_ids"][arg]
        except KeyError:
            raise KeyError(f"falta notebook_ids['{arg}'] en pipelines/local.json") from None
    if key not in SIMPLE:
        raise KeyError(f"marcador desconocido: {{{{{key}}}}}")
    try:
        return cfg[SIMPLE[key]]
    except KeyError:
        raise KeyError(f"falta '{SIMPLE[key]}' en pipelines/local.json") from None


def missing_notebooks(template_text: str, cfg: dict) -> list:
    """Nombres de cuaderno que la plantilla pide y que no están en notebook_ids."""
    have = cfg.get("notebook_ids", {})
    return sorted({arg for key, arg in placeholders_in(template_text) if key == "NOTEBOOK_ID" and arg not in have})


def parse_ids_text(text: str) -> dict:
    """Líneas "nombre id" (p. ej. la salida de notebookutils.notebook.list()) -> {nombre: id}. Ignora lo demás."""
    ids = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and GUID.fullmatch(parts[-1]):
            ids[" ".join(parts[:-1])] = parts[-1]
    return ids


def check_graph(pipeline: dict) -> None:
    """Nombres únicos, dependencias existentes, condiciones válidas y sin ciclos."""
    acts = pipeline["properties"]["activities"]
    names = [a["name"] for a in acts]
    if len(names) != len(set(names)):
        raise ValueError("nombres de actividad repetidos")
    graph = {}
    for a in acts:
        deps = a.get("dependsOn", [])
        for d in deps:
            bad = set(d["dependencyConditions"]) - CONDITIONS
            if bad:
                raise ValueError(f"{a['name']}: condición inválida {sorted(bad)}")
        graph[a["name"]] = [d["activity"] for d in deps]
    validate_dag(graph)          # lanza ValueError si hay dependencias inexistentes o ciclos


def render(template_text: str, cfg: dict) -> str:
    """Rellena los marcadores, valida el resultado y lo devuelve como JSON."""
    text = PLACEHOLDER.sub(lambda m: resolve(m.group(1), m.group(2), cfg), template_text)
    pipeline = json.loads(text)
    check_graph(pipeline)
    return json.dumps(pipeline, indent=4, ensure_ascii=False) + "\n"


def to_template(exported: dict, cfg: dict) -> str:
    """JSON exportado del portal -> plantilla: quita campos del sistema y cambia los valores reales por marcadores.
    Falla si queda algún GUID o correo sin marcador, para no filtrar nada al repo público."""
    data = {k: v for k, v in exported.items() if k not in SYSTEM_FIELDS}
    props = dict(data.get("properties", {}))
    for k in SYSTEM_FIELDS:
        props.pop(k, None)
    data["properties"] = props
    text = json.dumps(data, indent=4, ensure_ascii=False)
    pairs = [(v, f"{{{{{k}}}}}") for k, ck in SIMPLE.items() if (v := cfg.get(ck))]
    pairs += [(v, f"{{{{NOTEBOOK_ID:{name}}}}}") for name, v in cfg.get("notebook_ids", {}).items()]
    for real, marker in sorted(pairs, key=lambda p: -len(p[0])):
        text = text.replace(real, marker)
    leftovers = sorted(set(GUID.findall(text)) | set(EMAIL.findall(text)))
    if leftovers:
        raise ValueError("quedan identificadores sin marcador (agrégalos a pipelines/local.json): "
                         + ", ".join(leftovers))
    return text + "\n"


def load_local() -> dict:
    if not LOCAL.exists():
        raise SystemExit("falta pipelines/local.json: copia pipelines/local.example.json y complétalo")
    return json.loads(LOCAL.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("render")
    r.add_argument("name")
    i = sub.add_parser("ids-from-text")
    i.add_argument("file")
    t = sub.add_parser("templatize")
    t.add_argument("file")
    t.add_argument("--name")
    a = ap.parse_args(argv)

    if a.cmd == "list":
        for p in sorted(TEMPLATES.glob("*.template.json")):
            print(p.name.removesuffix(".template.json"))
    elif a.cmd == "render":
        template = (TEMPLATES / f"{a.name}.template.json").read_text(encoding="utf-8")
        cfg = load_local()
        missing = missing_notebooks(template, cfg)
        if missing:
            names = "\n  ".join(missing)
            raise SystemExit(f"faltan {len(missing)} ids de cuaderno en pipelines/local.json (notebook_ids):\n  {names}\n"
                             "Obtenlos con notebookutils.notebook.list() y corre: "
                             "python scripts/pipeline_tool.py ids-from-text <archivo>")
        out = render(template, cfg)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / f"{a.name}.json").write_text(out, encoding="utf-8")
        print(f"listo: {OUTPUT / (a.name + '.json')}  (pégalo en la vista de código JSON del pipeline)")
    elif a.cmd == "ids-from-text":
        found = parse_ids_text(pathlib.Path(a.file).read_text(encoding="utf-8"))
        cfg = load_local()
        cfg.setdefault("notebook_ids", {}).update(found)
        LOCAL.write_text(json.dumps(cfg, indent=4, ensure_ascii=False) + chr(10), encoding="utf-8")
        print(f"{len(found)} ids guardados en pipelines/local.json (no se muestran)")
    else:
        exported = json.loads(pathlib.Path(a.file).read_text(encoding="utf-8"))
        name = a.name or exported["name"]
        out = to_template(exported, load_local())
        TEMPLATES.mkdir(parents=True, exist_ok=True)
        (TEMPLATES / f"{name}.template.json").write_text(out, encoding="utf-8")
        print(f"plantilla actualizada: pipelines/templates/{name}.template.json")


if __name__ == "__main__":
    main()
