"""Etapa 3 (§18, Tabla 8): cuadernos de liquidación como funciones puras sobre la base de cruces.

Los criterios y reglas son DATOS (tablas param.*), no código. Esta PoC solo implementa el motor
genérico (operadores =, !=, IN) y los pasos mínimos. Lo marcado ILUSTRATIVO no proviene del manual
de la SDIS (PENDIENTES G3 a G7)."""
import csv
import io
from collections import defaultdict

from .huella import sha256_bytes
from .params import hay_ilustrativos

# Nombre de campo usado en param.* -> columna de la base de cruces (Tabla 7)
ALIAS_CAMPOS = {"estado_validacion": "valor_validacion"}


def _cumple(fila, campo, operador, valor):
    actual = fila.get(ALIAS_CAMPOS.get(campo, campo))
    actual = None if actual is None else str(actual)
    if operador == "=":
        return actual == str(valor)
    if operador == "!=":
        return actual != str(valor)
    if operador == "IN":
        return actual in {v.strip() for v in str(valor).split(",")}
    raise ValueError(f"operador no soportado: {operador}")


# nb_00_focalizacion: elegibles y excluidos, cada exclusión con su causal
def focalizar(base, criterios, reglas_bloqueo):
    res = []
    for r in base:
        causales = [f"NO_CUMPLE_{c['criterio']}" for c in criterios
                    if not _cumple(r, c["campo"], c["operador"], c["valor"])]
        causales += [b["causal"] for b in reglas_bloqueo
                     if _cumple(r, b["campo"], b["operador"], b["valor"])]
        res.append({"id_ciclo": r["id_ciclo"], "id_persona": r["id_persona"], "id_hogar": r["id_hogar"],
                    "elegible": not causales, "causales": ";".join(causales) or None})
    return res


# nb_01_titular: un titular por hogar según el orden de criterios parametrizado
def seleccionar_titular(focalizacion, base, regla_titular):
    por_persona = {r["id_persona"]: r for r in base}
    candidatos = defaultdict(list)
    for f in focalizacion:
        if f["elegible"]:
            candidatos[f["id_hogar"]].append(por_persona[f["id_persona"]])
    orden = sorted(regla_titular, key=lambda x: x["orden"])
    titulares = []
    for hogar in sorted(candidatos):
        miembros = candidatos[hogar]
        for criterio in reversed(orden):  # orden estable: el primer criterio manda
            miembros = sorted(miembros, key=lambda m, c=criterio: str(m.get(c["criterio"]) or ""),
                              reverse=criterio["direccion"] == "DESC")
        t = miembros[0]
        titulares.append({"id_ciclo": t["id_ciclo"], "id_hogar": hogar, "id_persona": t["id_persona"],
                          "n_candidatos": len(miembros)})
    return titulares


# nb_02_medio_pago: ILUSTRATIVO. Sin datos financieros reales, se asigna el operador habilitado de
# mayor prioridad; si la base trae estado_producto, solo se asignan productos activos (no definido: G2).
def asignar_medio_pago(titulares, operadores):
    ops = sorted(operadores, key=lambda o: o["prioridad"])
    if not ops:
        raise ValueError("sin operadores habilitados vigentes")
    return [{**t, "operador": ops[0]["operador"], "modo": "stub_ilustrativo"} for t in titulares]


# nb_03_monto: ILUSTRATIVO, monto base por hogar desde param.montos
def calcular_monto(titulares, montos):
    base = next(m for m in montos if m["concepto"] == "MONTO_BASE_HOGAR")["monto"]
    return [{"id_ciclo": t["id_ciclo"], "id_hogar": t["id_hogar"], "id_persona": t["id_persona"],
             "monto": float(base), "componentes": f"MONTO_BASE_HOGAR={base}"} for t in titulares]


# nb_04_fuente_recursos: asigna la fuente con saldo y marca si se excede el techo (insumo del Control 3)
def asignar_fuente_recursos(montos, fuentes):
    saldo = {f["fuente_recursos"]: float(f["techo"]) for f in fuentes}
    orden = [f["fuente_recursos"] for f in fuentes]
    pagos, excedidos = [], 0
    for m in montos:
        fuente = next((f for f in orden if saldo[f] >= m["monto"]), orden[-1])
        if saldo[fuente] < m["monto"]:
            excedidos += 1
        saldo[fuente] -= m["monto"]
        pagos.append({**m, "fuente_recursos": fuente})
    return pagos, {"saldo": saldo, "pagos_sobre_techo": excedidos}


# nb_05_listados: archivos por operador y fuente + sábana del ciclo
def generar_listados(pagos, medio_pago, base):
    por_persona = {r["id_persona"]: r for r in base}
    op = {m["id_hogar"]: m["operador"] for m in medio_pago}
    filas = []
    for p in pagos:
        b = por_persona[p["id_persona"]]
        filas.append({"id_ciclo": p["id_ciclo"], "operador": op[p["id_hogar"]],
                      "fuente_recursos": p["fuente_recursos"], "id_hogar": p["id_hogar"],
                      "id_persona": p["id_persona"], "tipo_doc": b["tipo_doc"], "num_doc": b["num_doc"],
                      "nombres": b["nombres"], "apellidos": b["apellidos"], "monto": p["monto"]})
    sabana = sorted(filas, key=lambda f: (f["operador"], f["fuente_recursos"], f["id_hogar"]))
    por_archivo = defaultdict(list)
    for f in sabana:
        por_archivo[(f["operador"], f["fuente_recursos"])].append(f)
    return sabana, dict(por_archivo)


def _csv_bytes(filas):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(filas[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    return buf.getvalue().encode("utf-8")


def publicar(archivos, raiz, id_ciclo):
    """nb_07_publicar (adaptación de la PoC al §18.4): escribe {raiz}/{id_ciclo}/{operador}/ y un
    manifiesto SHA-256. En producción el destino es Azure Storage con política de inmutabilidad;
    aquí es OneLake Files (sin inmutabilidad). Devuelve el manifiesto."""
    import os

    manifiesto = []
    for (operador, fuente), filas in sorted(archivos.items()):
        carpeta = os.path.join(raiz, id_ciclo, operador)
        os.makedirs(carpeta, exist_ok=True)
        datos = _csv_bytes(filas)
        nombre = f"listado_{operador}_{fuente}.csv"
        with open(os.path.join(carpeta, nombre), "wb") as f:
            f.write(datos)
        manifiesto.append({"archivo": f"{operador}/{nombre}", "filas": len(filas),
                           "sha256": sha256_bytes(datos)})
    with open(os.path.join(raiz, id_ciclo, "manifest_sha256.csv"), "wb") as f:
        f.write(_csv_bytes(manifiesto))
    return manifiesto


# nb_06_informe: contenido mínimo del §18.4
def armar_informe(*, id_ciclo, fecha_corte, version_fuentes, parametros_aplicados, versiones_cuadernos,
                  base, focalizacion, titulares, pagos, sabana, aprobaciones):
    exclusiones = defaultdict(int)
    for f in focalizacion:
        for c in (f["causales"] or "").split(";"):
            if c:
                exclusiones[c] += 1
    total_pagos = sum(p["monto"] for p in pagos)
    total_listados = sum(f["monto"] for f in sabana)
    totales = defaultdict(float)
    for f in sabana:
        totales[("operador", f["operador"])] += f["monto"]
        totales[("fuente", f["fuente_recursos"])] += f["monto"]
    aplicados = [p for lista in parametros_aplicados.values() for p in lista]
    return {
        "id_ciclo": id_ciclo, "fecha_corte": fecha_corte, "version_fuentes": version_fuentes,
        "parametros_aplicados": {k: len(v) for k, v in parametros_aplicados.items()},
        "usa_parametros_ilustrativos": hay_ilustrativos(aplicados),
        "versiones_cuadernos": versiones_cuadernos,
        "conteos": {"universo": len(base), "elegibles": sum(1 for f in focalizacion if f["elegible"]),
                    "titulares": len(titulares), "pagos_liquidados": len(pagos)},
        "exclusiones_por_causal": dict(exclusiones),
        "totales_por_operador": {k[1]: v for k, v in totales.items() if k[0] == "operador"},
        "totales_por_fuente": {k[1]: v for k, v in totales.items() if k[0] == "fuente"},
        "verificacion_suma_listados_igual_liquidacion": abs(total_pagos - total_listados) < 1e-6,
        "aprobaciones": aprobaciones,
    }
