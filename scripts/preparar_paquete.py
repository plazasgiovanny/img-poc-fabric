"""Arma salida/paquete_fabric/ con todo lo que hay que subir al trial de Fabric.

    python scripts/preparar_paquete.py [--n 500] [--semilla 20261002]

Contenido (en orden de uso, ver docs/ENV_CHECK.md):
  1_environment/   .whl de img_lib para el Environment env_img
  2_ddl/           SQL de control y parámetros (ejecutar en lh_control)
  3_datos/         Files/sinteticos/{landing,verdad}: subir a lh_control > Files
  4_notebooks/     cuadernos con VERSION_CUADERNO = SHA corto de git (trazabilidad del §18)
Los datos se regeneran con la semilla; salida/ está en .gitignore (repo público)."""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "generador"))
import generador  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=False).stdout.strip()


def version_git():
    sha = git("rev-parse", "--short", "HEAD") or "sin-git"
    sucio = bool(git("status", "--porcelain", "--", "notebooks", "img_lib", "ddl"))
    return f"{sha}-sin-commitear" if sucio else sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--semilla", type=int, default=generador.SEMILLA)
    a = ap.parse_args()

    destino = RAIZ / "salida" / "paquete_fabric"
    if destino.exists():
        shutil.rmtree(destino)
    ver = version_git()

    # 1) wheel
    subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(destino / "1_environment"),
                    str(RAIZ / "img_lib")], check=True, capture_output=True)
    # 2) ddl
    shutil.copytree(RAIZ / "ddl", destino / "2_ddl")
    # 3) datos sintéticos: dos cortes
    for corte in (1, 2):
        generador.escribir(generador.generar(a.n, corte, a.semilla), destino / "3_datos" / "Files" / "sinteticos", corte)
    # 4) cuadernos con la versión de git
    (destino / "4_notebooks").mkdir(parents=True)
    n = 0
    for f in sorted((RAIZ / "notebooks").glob("*.py")):
        txt = f.read_text(encoding="utf-8")
        txt, k = re.subn(r'VERSION_CUADERNO = "dev"', f'VERSION_CUADERNO = "{ver}"', txt)
        (destino / "4_notebooks" / f.name).write_text(txt, encoding="utf-8")
        n += 1
    print(f"paquete en {destino}\n  versión: {ver}\n  cuadernos: {n}\n  registros por fuente (corte 1): "
          f"{sum(1 for _ in open(destino / '3_datos/Files/sinteticos/landing/corte1/poblacional.csv', encoding='utf-8')) - 1}")


if __name__ == "__main__":
    main()
