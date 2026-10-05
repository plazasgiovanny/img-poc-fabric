import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import notebook_tool as nt  # noqa: E402

NOTEBOOKS = sorted((ROOT / "notebooks").glob("nb_*.py"))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_parameters_cell_is_separate_and_tagged(path):
    cells = nt.to_ipynb(path.read_text(encoding="utf-8"))["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    tagged = [c for c in code if "parameters" in c["metadata"].get("tags", [])]
    assert len(code) >= 2 and len(tagged) == 1 and code[0] is tagged[0]
    assert "spark" not in "".join(tagged[0]["source"])          # la celda de parámetros no ejecuta nada


def test_source_roundtrip_keeps_code():
    text = "# cabecera\n\n# %% Parámetros\na = 1\n\n# %% Ejecución\nprint(a)\n"
    cells = nt.to_ipynb(text)["cells"]
    assert [c["cell_type"] for c in cells] == ["markdown", "code", "code"]
    assert "".join(cells[1]["source"]) == "a = 1" and "".join(cells[2]["source"]) == "print(a)"
