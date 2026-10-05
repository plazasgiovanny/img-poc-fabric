"""Convierte los cuadernos `# %%` de notebooks/ a .ipynb para importarlos a Fabric con las celdas separadas.

El importador de .py de Fabric ignora los marcadores `# %%` y deja todo en una sola celda, por lo que la
celda de parámetros contendría también la ejecución y los argumentos del pipeline llegarían tarde.
En el .ipynb la celda cuyo título empieza por "Parámetros" lleva la etiqueta `parameters`.
No se escriben IDs de lakehouse (el repo es público): el lakehouse por defecto se asocia en Fabric.

    python scripts/notebook_tool.py notebooks/nb_init_cycle.py [salida_dir]
"""
import json
import re
import sys
from pathlib import Path

MARKER = re.compile(r"^# %%(.*)$", re.MULTILINE)
FABRIC_CELL = {"microsoft": {"language": "python", "language_group": "synapse_pyspark"}}


def _lines(text: str) -> list:
    lines = text.strip("\n").split("\n")
    return [line + "\n" for line in lines[:-1]] + [lines[-1]] if lines != [""] else []


def to_ipynb(text: str) -> dict:
    """Parte el texto por marcadores `# %%`. El encabezado previo al primero pasa a una celda markdown."""
    parts = MARKER.split(text)          # [encabezado, título1, cuerpo1, título2, cuerpo2, ...]
    cells = []
    header = parts[0].strip()
    if header:
        md = "\n".join(re.sub(r"^# ?", "", ln) for ln in header.split("\n"))
        cells.append({"cell_type": "markdown", "metadata": {}, "source": _lines(md)})
    for title, body in zip(parts[1::2], parts[2::2], strict=True):
        meta = dict(FABRIC_CELL)
        if title.strip().lower().startswith("parámetros"):
            meta["tags"] = ["parameters"]
        cells.append({"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
                      "source": _lines(body)})
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernel_info": {"name": "synapse_pyspark"},
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark"},
            "language_info": {"name": "python"},
            "microsoft": {"language": "python", "language_group": "synapse_pyspark"},
        },
        "cells": cells,
    }


def write(src: Path, out_dir: Path, replace: dict = None) -> Path:
    text = src.read_text(encoding="utf-8")
    for old, new in (replace or {}).items():
        text = text.replace(old, new)
    target = out_dir / (src.stem + ".ipynb")
    target.write_text(json.dumps(to_ipynb(text), ensure_ascii=False, indent=1), encoding="utf-8")
    return target


if __name__ == "__main__":
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output")
    out.mkdir(parents=True, exist_ok=True)
    print(write(Path(sys.argv[1]), out))
