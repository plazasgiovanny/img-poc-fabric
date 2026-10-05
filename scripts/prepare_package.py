"""Arma output/fabric_package/ con todo lo que hay que subir al trial de Fabric.

    python scripts/prepare_package.py [--n 500] [--seed 20261002]

Contenido (en orden de uso, ver docs/ENV_CHECK.md):
  1_environment/   .whl de img_lib para el Environment env_img
  2_ddl/           SQL de control y parámetros (ejecutar en lh_control)
  3_data/          Files/synthetic/{landing,ground_truth}: subir a lh_control > Files
  4_notebooks/     cuadernos .ipynb (celdas separadas, celda de parámetros etiquetada) con NOTEBOOK_VERSION = SHA corto de git (trazabilidad del §18)
Los datos se regeneran con la semilla; output/ está en .gitignore (repo público)."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "generator"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import notebook_tool  # noqa: E402

import generator  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False).stdout.strip()


def git_version():
    sha = git("rev-parse", "--short", "HEAD") or "no-git"
    dirty = bool(git("status", "--porcelain", "--", "notebooks", "img_lib", "ddl"))
    return f"{sha}-uncommitted" if dirty else sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=generator.SEED)
    a = ap.parse_args()

    destination = REPO_ROOT / "output" / "fabric_package"
    if destination.exists():
        shutil.rmtree(destination)
    view = git_version()

    # 1) wheel
    subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(destination / "1_environment"),
                    str(REPO_ROOT / "img_lib")], check=True, capture_output=True)
    # 2) ddl
    shutil.copytree(REPO_ROOT / "ddl", destination / "2_ddl")
    # 3) datos sintéticos: dos cortes
    for cutoff in (1, 2):
        generator.write(generator.generate(a.n, cutoff, a.seed), destination / "3_data" / "Files" / "synthetic", cutoff)
    # 4) cuadernos con la versión de git
    (destination / "4_notebooks").mkdir(parents=True)
    n = 0
    for f in sorted((REPO_ROOT / "notebooks").glob("*.py")):
        notebook_tool.write(f, destination / "4_notebooks", {'NOTEBOOK_VERSION = "dev"': f'NOTEBOOK_VERSION = "{view}"'})
        n += 1
    print(f"package at {destination}\n  version: {view}\n  notebooks: {n}\n  records per source (cutoff 1): "
          f"{sum(1 for _ in open(destination / '3_data/Files/synthetic/landing/cutoff1/population.csv', encoding='utf-8')) - 1}")


if __name__ == "__main__":
    main()
