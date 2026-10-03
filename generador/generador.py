"""Generador de datos SINTÉTICOS para la PoC IMG (Ley 1581 de 2012: no hay datos personales reales).

- Determinista: misma semilla => mismos datos. Los datos NO se versionan (ver .gitignore).
- Documentos en rango imposible (prefijo 99 + 8 dígitos) para no chocar con personas reales.
- ESQUEMA PROVISIONAL (PENDIENTE G2): se ajusta cuando el equipo entregue el diccionario de las
  dos fuentes. Los campos siguen la Tabla 7 del documento (nombres de referencia).
- Inyecta defectos controlados y escribe la "verdad conocida" para medir errores (<1 %, §7 Exp. 2).

Uso local:  python generador.py --n 500 --corte 1 --salida data/
En Fabric: importar `generar()` y escribir a lh_control/Files/sinteticos/{landing,verdad}."""
import argparse
import csv
import random
from pathlib import Path

SEMILLA = 20261002
TASAS = {  # parametrizables
    "dup_exacto": 0.02, "variante_nombre": 0.02, "homonimo": 0.01, "doc_malformado": 0.015,
    "fecha_o_localidad_invalida": 0.01, "no_encontrado_validacion": 0.05, "fallecido": 0.03,
    "hogar_multi_titular": 0.05, "cambio_corte2": 0.03,
}
NOMBRES = ["María", "José", "Luz", "Carlos", "Ana", "Juan", "Sandra", "Luis", "Marta", "Pedro",
           "Diana", "Jorge", "Paola", "Andrés", "Rosa", "Camilo", "Nelly", "Fabián", "Yolanda", "Iván"]
APELLIDOS = ["Rodríguez", "Gómez", "Martínez", "López", "Pérez", "Ramírez", "Torres", "Castro",
             "Rojas", "Moreno", "Díaz", "Vargas", "Muñoz", "Ortiz", "Cárdenas", "Peña", "Suárez"]
GRUPOS = ["A", "B", "C", "D"]

CAMPOS_POB = ["id_origen", "id_hogar_origen", "tipo_doc", "num_doc", "nombres", "apellidos",
              "fecha_nacimiento", "localidad", "direccion", "grupo_sisben", "subgrupo_sisben",
              "fecha_encuesta"]
CAMPOS_VAL = ["id_origen", "tipo_doc", "num_doc", "nombres", "apellidos", "estado", "fecha_corte"]
CAMPOS_VERDAD = ["fuente", "id_origen", "id_persona_real", "id_hogar_real", "defectos",
                 "va_a_cuarentena", "estado_real"]


def _variante(rng, s):
    """Variante realista de un nombre: tilde perdida, letra cambiada o espacio extra."""
    k = rng.choice(("sin_tilde", "typo", "espacios"))
    if k == "sin_tilde":
        tabla = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
        t = s.translate(tabla)
        return t if t != s else s.upper()
    if k == "typo" and len(s) > 3:
        i = rng.randrange(1, len(s) - 1)
        return s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return f" {s}  "


def generar(n_personas=500, corte=1, semilla=SEMILLA, tasas=None):
    tasas = {**TASAS, **(tasas or {})}
    rng = random.Random(semilla)  # la base de personas es idéntica en cortes 1 y 2
    fecha_corte = "2026-09-30" if corte == 1 else "2026-10-31"

    # ---- población real (verdad) ----
    reales, hogares, n_h = [], {}, 0
    for i in range(n_personas):
        if not hogares or rng.random() > 0.55:  # ~1.8 personas por hogar
            n_h += 1
            hogares[n_h] = rng.randrange(1, 21)
        h = n_h
        reales.append({
            "id_persona_real": f"R{i + 1:06d}", "id_hogar_real": f"HR{h:05d}",
            "tipo_doc": "CC", "num_doc": f"99{rng.randrange(10**7, 10**8)}",
            "nombres": rng.choice(NOMBRES), "apellidos": f"{rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}",
            "fecha_nacimiento": f"{rng.randrange(1950, 2008)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}",
            "localidad": f"{hogares[h]:02d}", "direccion": f"CL {rng.randrange(1, 200)} # {rng.randrange(1, 90)}-{rng.randrange(1, 99)}",
            "grupo": rng.choice(GRUPOS), "sub": rng.randrange(1, 8),
            "estado": "FALLECIDO" if rng.random() < tasas["fallecido"] else "VIVO",
        })
    # evita colisiones accidentales de documento
    vistos = set()
    for r in reales:
        while r["num_doc"] in vistos:
            r["num_doc"] = f"99{rng.randrange(10**7, 10**8)}"
        vistos.add(r["num_doc"])

    rng2 = random.Random(semilla + corte)  # cambios y defectos que varían por corte
    if corte == 2:  # ~3 % de cambios: nuevos fallecidos y cambios de localidad
        for r in reales:
            x = rng2.random()
            if x < tasas["cambio_corte2"] / 2:
                r["estado"] = "FALLECIDO"
            elif x < tasas["cambio_corte2"]:
                r["localidad"] = f"{rng2.randrange(1, 21):02d}"

    pob, val, verdad = [], [], []

    def fila_pob(r, idx, **over):
        f = {"id_origen": f"POB{idx:06d}", "id_hogar_origen": r["id_hogar_real"], "tipo_doc": r["tipo_doc"],
             "num_doc": r["num_doc"], "nombres": r["nombres"], "apellidos": r["apellidos"],
             "fecha_nacimiento": r["fecha_nacimiento"], "localidad": r["localidad"], "direccion": r["direccion"],
             "grupo_sisben": r["grupo"], "subgrupo_sisben": r["sub"], "fecha_encuesta": "2025-06-15"}
        f.update(over)
        return f

    def reg_verdad(fuente, f, r, defectos, cuarentena):
        verdad.append({"fuente": fuente, "id_origen": f["id_origen"], "id_persona_real": r["id_persona_real"],
                       "id_hogar_real": r["id_hogar_real"], "defectos": "|".join(defectos),
                       "va_a_cuarentena": int(cuarentena), "estado_real": r["estado"]})

    k = 0
    for r in reales:
        k += 1
        defectos, over, cuarentena = [], {}, False
        x = rng2.random()
        if x < tasas["doc_malformado"]:
            over["num_doc"] = r["num_doc"][:3] + "A" + r["num_doc"][4:]
            defectos, cuarentena = ["doc_malformado"], True
        elif x < tasas["doc_malformado"] + tasas["fecha_o_localidad_invalida"]:
            if rng2.random() < 0.5:
                over["fecha_nacimiento"] = "2099-01-01"
            else:
                over["localidad"] = "77"
            defectos, cuarentena = ["fecha_o_localidad_invalida"], True
        f = fila_pob(r, k, **over)
        pob.append(f)
        reg_verdad("poblacional", f, r, defectos, cuarentena)
        if cuarentena:
            continue
        y = rng2.random()
        if y < tasas["dup_exacto"]:
            k += 1
            d = {**f, "id_origen": f"POB{k:06d}"}
            pob.append(d)
            reg_verdad("poblacional", d, r, ["dup_exacto"], False)
        elif y < tasas["dup_exacto"] + tasas["variante_nombre"]:
            k += 1
            d = {**f, "id_origen": f"POB{k:06d}", "nombres": _variante(rng2, r["nombres"])}
            pob.append(d)
            reg_verdad("poblacional", d, r, ["variante_nombre"], False)
        elif y < tasas["dup_exacto"] + tasas["variante_nombre"] + tasas["homonimo"]:
            k += 1  # misma identidad aparente (nombre), OTRA persona (otro documento)
            otro = {**r, "id_persona_real": r["id_persona_real"] + "H", "id_hogar_real": r["id_hogar_real"] + "H",
                    "num_doc": f"99{rng2.randrange(10**7, 10**8)}",
                    "fecha_nacimiento": f"{rng2.randrange(1950, 2008)}-{rng2.randrange(1, 13):02d}-{rng2.randrange(1, 29):02d}"}
            d = fila_pob(otro, k, id_hogar_origen=otro["id_hogar_real"])
            pob.append(d)
            reg_verdad("poblacional", d, otro, ["homonimo"], False)

    # ---- fuente de validación (supervivencia) ----
    for j, r in enumerate(reales, 1):
        if rng2.random() < tasas["no_encontrado_validacion"]:
            continue
        v = {"id_origen": f"VAL{j:06d}", "tipo_doc": r["tipo_doc"], "num_doc": r["num_doc"],
             "nombres": r["nombres"], "apellidos": r["apellidos"], "estado": r["estado"], "fecha_corte": fecha_corte}
        val.append(v)
        reg_verdad("validacion", v, r, [], False)

    return {"poblacional": pob, "validacion": val, "verdad": verdad, "fecha_corte": fecha_corte}


def escribir(datos, salida, corte):
    salida = Path(salida)
    for sub, campos, clave in (("landing", CAMPOS_POB, "poblacional"), ("landing", CAMPOS_VAL, "validacion"),
                               ("verdad", CAMPOS_VERDAD, "verdad")):
        carpeta = salida / sub / f"corte{corte}"
        carpeta.mkdir(parents=True, exist_ok=True)
        with open(carpeta / f"{clave}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(datos[clave])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--corte", type=int, choices=(1, 2), default=1)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    ap.add_argument("--salida", default="data")
    a = ap.parse_args()
    d = generar(a.n, a.corte, a.semilla)
    escribir(d, a.salida, a.corte)
    print(f"poblacional={len(d['poblacional'])} validacion={len(d['validacion'])} -> {a.salida}")
