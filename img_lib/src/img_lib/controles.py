"""Resumen que se presenta al aprobador en cada control humano (Tabla 9, §19).

Los resúmenes son funciones puras sobre listas de dicts; los cuadernos aportan los datos de Delta.
El plazo vencido se trata como rechazo (§19)."""
from collections import Counter

CONTROLES = {  # Tabla 9: control -> (momento, responsable sugerido)
    "C1": ("Fuentes en Oro (cuarentena y conteos)", "Líder de datos"),
    "C2": ("Base de cruces (% de coincidencia por fuente)", "Analista líder"),
    "C3": ("Liquidación (causales, montos frente al techo)", "Líder funcional de transferencias"),
    "C4": ("Listados e informe", "Responsable del programa"),
}
DECISIONES = {"PENDIENTE", "APROBADO", "RECHAZADO", "VENCIDO"}


def resumen_c1(entregas, cuarentena, oro_por_fuente):
    return {"control": "C1", "momento": CONTROLES["C1"][0],
            "entregas": [{k: e[k] for k in ("fuente", "n_registros", "sha256")} for e in entregas],
            "cuarentena_por_causa": dict(Counter(c["causa"] for c in cuarentena)),
            "registros_en_oro": oro_por_fuente}


def resumen_c2(base, pct):
    return {"control": "C2", "momento": CONTROLES["C2"][0], "universo": len(base),
            "pct_coincidencia_validacion": round(pct, 2)}


def resumen_c3(focalizacion, pagos, estado_fuentes, fuentes):
    techo = {f["fuente_recursos"]: float(f["techo"]) for f in fuentes}
    causales = Counter(c for f in focalizacion for c in (f["causales"] or "").split(";") if c)
    return {"control": "C3", "momento": CONTROLES["C3"][0],
            "elegibles": sum(1 for f in focalizacion if f["elegible"]),
            "exclusiones_por_causal": dict(causales),
            "monto_total": sum(p["monto"] for p in pagos), "techo_por_fuente": techo,
            "pagos_sobre_techo": estado_fuentes["pagos_sobre_techo"]}


def resumen_c4(informe):
    return {"control": "C4", "momento": CONTROLES["C4"][0], "conteos": informe["conteos"],
            "suma_listados_igual_liquidacion": informe["verificacion_suma_listados_igual_liquidacion"],
            "usa_parametros_ilustrativos": informe["usa_parametros_ilustrativos"]}


def fila_aprobacion(*, id_ciclo, control, decision, aprobador, mecanismo, solicitado_en, decidido_en,
                    comentario=None, pipeline_run_id=None):
    if control not in CONTROLES:
        raise ValueError(f"control desconocido: {control}")
    if decision not in DECISIONES:
        raise ValueError(f"decisión inválida: {decision}")
    return {"id_ciclo": id_ciclo, "control": control, "rol_responsable": CONTROLES[control][1],
            "solicitado_en": solicitado_en, "decidido_en": decidido_en, "decision": decision,
            "aprobador": aprobador, "comentario": comentario, "mecanismo": mecanismo,
            "pipeline_run_id": pipeline_run_id}


def todas_aprobadas(filas, id_ciclo, controles=("C1", "C2", "C3", "C4")):
    """Último estado por control: solo APROBADO cuenta. Pendiente, vencido o ausente = no aprobado."""
    ultimo = {}
    por_fecha = sorted((f for f in filas if f["id_ciclo"] == id_ciclo),
                       key=lambda f: f["decidido_en"] or f["solicitado_en"] or "")
    for f in por_fecha:
        ultimo[f["control"]] = f["decision"]
    return all(ultimo.get(c) == "APROBADO" for c in controles)
