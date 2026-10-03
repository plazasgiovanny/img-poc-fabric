"""Cadena lógica completa (Plata -> MDM -> Oro -> cruces -> liquidación -> listados -> informe) sobre
datos sintéticos, sin Spark. Verifica los criterios de la PoC antes de llevarla a Fabric."""
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "img_lib" / "src"))
sys.path.insert(0, str(ROOT / "generador"))

from img_lib.validar import validar_registro

import generador
from img_lib import cruces, liquidacion, mdm, metricas, vigentes
from img_lib import ilustrativos as ilu

HOY = date(2026, 10, 1)
CORTE = "2026-09-30"


def correr(n=500, corte=1):
    datos = generador.generar(n, corte)
    plata, cuarentena = [], []
    for fuente in ("poblacional", "validacion"):
        for r in datos[fuente]:
            reg, causas = validar_registro({**r, "fuente": fuente}, hoy=HOY)
            (cuarentena if causas else plata).append(reg)
    personas, xref = mdm.construir_maestro(plata)
    _, asign = mdm.construir_hogares(personas)
    persona_de = {(x["fuente"], x["id_origen"]): x["id_persona"] for x in xref}
    oro = {"poblacional": [], "validacion": []}
    for r in plata:
        idp = persona_de[(r["fuente"], r["id_origen"])]
        oro[r["fuente"]].append({**r, "id_persona": idp, "id_hogar": asign[idp]})
    base = cruces.construir_base(oro["poblacional"], oro["validacion"], id_ciclo="2026-09", fecha_corte=CORTE,
                                 version_fuentes={"poblacional": "c1", "validacion": "c1"},
                                 id_ejecucion="E-test", version_cuaderno="test", ts="2026-10-01T00:00:00")
    p = {k: vigentes(getattr(ilu, k), CORTE) for k in
         ("CRITERIOS_FOCALIZACION", "REGLAS_BLOQUEO", "REGLA_TITULAR", "OPERADORES", "MONTOS", "FUENTES_RECURSOS")}
    foc = liquidacion.focalizar(base, p["CRITERIOS_FOCALIZACION"], p["REGLAS_BLOQUEO"])
    tit = liquidacion.seleccionar_titular(foc, base, p["REGLA_TITULAR"])
    mp = liquidacion.asignar_medio_pago(tit, p["OPERADORES"])
    mon = liquidacion.calcular_monto(tit, p["MONTOS"])
    pagos, estado = liquidacion.asignar_fuente_recursos(mon, p["FUENTES_RECURSOS"])
    sabana, archivos = liquidacion.generar_listados(pagos, mp, base)
    return dict(datos=datos, cuarentena=cuarentena, xref=xref, base=base, p=p, foc=foc, tit=tit, pagos=pagos,
                estado=estado, sabana=sabana, archivos=archivos)


def test_cadena_completa_y_criterios():
    c = correr()
    v = c["datos"]["verdad"]
    # base de cruces: una fila por persona, con los grupos de la Tabla 7
    ids = [r["id_persona"] for r in c["base"]]
    assert len(ids) == len(set(ids))
    for campo in ("id_ciclo", "id_persona", "id_hogar", "grupo_sisben", "encontrado_validacion", "id_ejecucion"):
        assert campo in c["base"][0]
    # un titular por hogar elegible
    hogares_elegibles = {f["id_hogar"] for f in c["foc"] if f["elegible"]}
    assert {t["id_hogar"] for t in c["tit"]} == hogares_elegibles and len(c["tit"]) == len(hogares_elegibles)
    # el titular es elegible
    elegibles = {f["id_persona"] for f in c["foc"] if f["elegible"]}
    assert all(t["id_persona"] in elegibles for t in c["tit"])
    # error de bloqueo < 1 % contra la verdad conocida
    def esperado(i):
        s = set()
        if i["fallecido"] and i["en_validacion"]:
            s.add("FALLECIDO_EN_VALIDACION")
        if not i["en_validacion"]:
            s.add("NO_ENCONTRADO_EN_VALIDACION")
        return s
    causales = [b["causal"] for b in c["p"]["REGLAS_BLOQUEO"]]
    assert metricas.tasa_error_bloqueo(v, c["xref"], c["foc"], esperado, causales) < 0.01
    # suma de listados == liquidación
    assert abs(sum(f["monto"] for f in c["sabana"]) - sum(p["monto"] for p in c["pagos"])) < 1e-6
    assert 0 < cruces.pct_coincidencia(c["base"]) < 100


def test_informe_publicacion_y_huella(tmp_path):
    c = correr()
    inf = liquidacion.armar_informe(
        id_ciclo="2026-09", fecha_corte=CORTE, version_fuentes={"poblacional": "c1"},
        parametros_aplicados=c["p"], versiones_cuadernos={"nb_00": "test"}, base=c["base"],
        focalizacion=c["foc"], titulares=c["tit"], pagos=c["pagos"], sabana=c["sabana"], aprobaciones=[])
    assert inf["usa_parametros_ilustrativos"] is True  # R8: debe verse en el informe
    assert inf["verificacion_suma_listados_igual_liquidacion"] is True
    assert inf["conteos"]["pagos_liquidados"] == len(c["tit"])
    man = liquidacion.publicar(c["archivos"], str(tmp_path), "2026-09")
    assert man and (tmp_path / "2026-09" / "manifest_sha256.csv").exists()
    from img_lib import sha256_archivo
    for m in man:
        assert sha256_archivo(str(tmp_path / "2026-09" / m["archivo"])) == m["sha256"]
    with open(tmp_path / "2026-09" / man[0]["archivo"], encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == man[0]["filas"]


def test_auditoria_cobertura():
    assert metricas.cobertura_auditoria(["E1", "E1", "E2"], ["E1", "E2"]) == 1.0
    assert metricas.cobertura_auditoria(["E1", "E3"], ["E1"]) == 0.5


def test_error_mdm_y_cuarentena_a_5000():
    c = correr(5000)
    v = c["datos"]["verdad"]
    assert metricas.tasa_error_mdm(v, c["xref"]) < 0.01
    ids = {(("poblacional" if r["id_origen"].startswith("POB") else "validacion"), r["id_origen"])
           for r in c["cuarentena"]}
    assert metricas.tasa_error_cuarentena(v, ids) < 0.01
