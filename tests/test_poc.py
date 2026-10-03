import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "img_lib" / "src"))
sys.path.insert(0, str(ROOT / "generador"))

from img_lib.params import hay_ilustrativos
from img_lib.validar import validar_llaves, validar_registro

import generador
from img_lib import (
    bitacora,
    mdm,
    normalizar_documento,
    normalizar_nombre,
    sha256_bytes,
    vigentes,
)

HOY = date(2026, 10, 1)


def test_normalizar_documento():
    assert normalizar_documento("99.123.456") == ("99123456", None)
    assert normalizar_documento("99A123456")[1] == "documento_no_numerico"
    assert normalizar_documento("123")[1] == "documento_longitud_invalida"
    assert normalizar_documento("")[1] == "documento_vacio"


def test_normalizar_nombre():
    assert normalizar_nombre("  José  Muñoz ") == ("JOSE MUÑOZ", None)
    assert normalizar_nombre(None)[1] == "nombre_vacio"


def test_huella_estable():
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_parametros_vigentes():
    filas = [
        {"k": "a", "vigente_desde": "2026-01-01", "vigente_hasta": None, "es_ilustrativo": 1},
        {"k": "b", "vigente_desde": "2025-01-01", "vigente_hasta": "2025-12-31"},
        {"k": "c", "vigente_desde": "2026-12-01", "vigente_hasta": None},
    ]
    v = vigentes(filas, "2026-09-30")
    assert [f["k"] for f in v] == ["a"] and hay_ilustrativos(v)


def test_validar_llaves():
    assert validar_llaves([{"a": 1}, {"a": 1}, {"a": None}], ["a"])


def test_bitacora_campos():
    e = bitacora.evento(id_ciclo="2026-09", id_ejecucion="E1", cuaderno="nb", version_cuaderno="v",
                        etapa_proceso="bronce", evento_trazabilidad="fin")
    assert all(c in e for c in bitacora.CAMPOS_INSTRUMENTO_A + bitacora.CAMPOS_TRAZABILIDAD)
    assert e["id_lote"] == "E1"


def test_generador_determinista_y_defectos():
    a = generador.generar(500, 1)
    b = generador.generar(500, 1)
    assert a == b
    defectos = "|".join(v["defectos"] for v in a["verdad"])
    for d in ("doc_malformado", "dup_exacto", "variante_nombre"):
        assert d in defectos
    assert all(r["num_doc"].startswith("99") for r in a["poblacional"] if r["num_doc"][:2].isdigit())


def test_pipeline_logico_contra_verdad():
    """Plata + MDM contra la verdad conocida: error < 1 % en cuarentena y en unificación de personas."""
    datos = generador.generar(500, 1)
    verdad = {(v["fuente"], v["id_origen"]): v for v in datos["verdad"]}
    plata, cuarentena = [], []
    for fuente in ("poblacional", "validacion"):
        for r in datos[fuente]:
            reg, causas = validar_registro({**r, "fuente": fuente}, hoy=HOY)
            (cuarentena if causas else plata).append(reg)

    # cuarentena: exactamente lo que la verdad dice
    esperados = {k for k, v in verdad.items() if v["va_a_cuarentena"]}
    obtenidos = {(("poblacional" if r["id_origen"].startswith("POB") else "validacion"), r["id_origen"])
                 for r in cuarentena}
    errores_q = len(esperados ^ obtenidos)
    assert errores_q / len(verdad) < 0.01

    _, xref = mdm.construir_maestro(plata)
    por_id = {}
    for x in xref:
        por_id.setdefault(x["id_persona"], set()).add(verdad[(x["fuente"], x["id_origen"])]["id_persona_real"])
    mezclas = sum(1 for s in por_id.values() if len(s) > 1)  # personas distintas unidas (falso positivo)
    real_a_ids = {}
    for x in xref:
        real_a_ids.setdefault(verdad[(x["fuente"], x["id_origen"])]["id_persona_real"], set()).add(x["id_persona"])
    partidas = sum(1 for s in real_a_ids.values() if len(s) > 1)  # una persona partida (falso negativo)
    assert (mezclas + partidas) / len(real_a_ids) < 0.01


def test_corte2_cambia_pocos():
    c1, c2 = generador.generar(500, 1), generador.generar(500, 2)
    est1 = {v["id_persona_real"]: v["estado_real"] for v in c1["verdad"]}
    est2 = {v["id_persona_real"]: v["estado_real"] for v in c2["verdad"]}
    cambios = sum(1 for k in est1 if k in est2 and est1[k] != est2[k])
    assert 0 < cambios < 0.05 * len(est1)
