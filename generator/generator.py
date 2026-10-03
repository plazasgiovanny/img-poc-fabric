"""Generador de datos SINTÉTICOS para la PoC IMG (Ley 1581 de 2012: no hay datos personales reales).

- Determinista: misma semilla => mismos datos. Los datos NO se versionan (ver .gitignore).
- Documentos en rango imposible (prefijo 99 + 8 dígitos) para no chocar con personas reales.
- ESQUEMA PROVISIONAL (PENDIENTE G2): se ajusta cuando el equipo entregue el diccionario de las
  dos fuentes. Los campos siguen la Tabla 7 del documento (nombres de referencia).
- Inyecta defectos controlados y escribe la "verdad conocida" para medir errores (<1 %, §7 Exp. 2).

Uso local:  python generator.py --n 500 --cutoff 1 --output data/
En Fabric: importar `generate()` y escribir a lh_control/Files/synthetic/{landing,ground_truth}."""
import argparse
import csv
import random
from pathlib import Path

SEED = 20261002
RATES = {  # parametrizables
    "exact_duplicate": 0.02, "name_variant": 0.02, "homonym": 0.01, "malformed_doc": 0.015,
    "invalid_date_or_locality": 0.01, "not_found_in_validation": 0.05, "deceased": 0.03,
    "multi_holder_household": 0.05, "cutoff2_change": 0.03,
}
FIRST_NAMES = ["María", "José", "Luz", "Carlos", "Ana", "Juan", "Sandra", "Luis", "Marta", "Pedro",
           "Diana", "Jorge", "Paola", "Andrés", "Rosa", "Camilo", "Nelly", "Fabián", "Yolanda", "Iván"]
LAST_NAMES = ["Rodríguez", "Gómez", "Martínez", "López", "Pérez", "Ramírez", "Torres", "Castro",
             "Rojas", "Moreno", "Díaz", "Vargas", "Muñoz", "Ortiz", "Cárdenas", "Peña", "Suárez"]
GROUPS = ["A", "B", "C", "D"]

POPULATION_FIELDS = ["origin_id", "origin_household_id", "doc_type", "doc_number", "first_names", "last_names",
              "birth_date", "locality", "address", "sisben_group", "sisben_subgroup",
              "survey_date"]
VALIDATION_FIELDS = ["origin_id", "doc_type", "doc_number", "first_names", "last_names", "status", "cutoff_date"]
GROUND_TRUTH_FIELDS = ["source", "origin_id", "true_person_id", "true_household_id", "defects",
                 "goes_to_quarantine", "true_status"]


def _variant(rng, s):
    """Variante realista de un nombre: tilde perdida, letra cambiada o espacio extra."""
    k = rng.choice(("no_accent", "typo", "spaces"))
    if k == "no_accent":
        table = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
        t = s.translate(table)
        return t if t != s else s.upper()
    if k == "typo" and len(s) > 3:
        i = rng.randrange(1, len(s) - 1)
        return s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return f" {s}  "


def generate(n_people=500, cutoff=1, seed=SEED, rates=None):
    rates = {**RATES, **(rates or {})}
    rng = random.Random(seed)  # la base de personas es idéntica en cortes 1 y 2
    cutoff_date = "2026-09-30" if cutoff == 1 else "2026-10-31"

    # ---- población real (verdad) ----
    true_people, households, n_h = [], {}, 0
    for i in range(n_people):
        if not households or rng.random() > 0.55:  # ~1.8 personas por hogar
            n_h += 1
            households[n_h] = rng.randrange(1, 21)
        h = n_h
        true_people.append({
            "true_person_id": f"R{i + 1:06d}", "true_household_id": f"HR{h:05d}",
            "doc_type": "CC", "doc_number": f"99{rng.randrange(10**7, 10**8)}",
            "first_names": rng.choice(FIRST_NAMES), "last_names": f"{rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}",
            "birth_date": f"{rng.randrange(1950, 2008)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}",
            "locality": f"{households[h]:02d}", "address": f"CL {rng.randrange(1, 200)} # {rng.randrange(1, 90)}-{rng.randrange(1, 99)}",
            "group": rng.choice(GROUPS), "sub": rng.randrange(1, 8),
            "status": "DECEASED" if rng.random() < rates["deceased"] else "ALIVE",
        })
    # evita colisiones accidentales de documento
    seen = set()
    for r in true_people:
        while r["doc_number"] in seen:
            r["doc_number"] = f"99{rng.randrange(10**7, 10**8)}"
        seen.add(r["doc_number"])

    rng2 = random.Random(seed + cutoff)  # cambios y defectos que varían por corte
    if cutoff == 2:  # ~3 % de cambios: nuevos fallecidos y cambios de localidad
        for r in true_people:
            x = rng2.random()
            if x < rates["cutoff2_change"] / 2:
                r["status"] = "DECEASED"
            elif x < rates["cutoff2_change"]:
                r["locality"] = f"{rng2.randrange(1, 21):02d}"

    pop, val, ground_truth = [], [], []

    def pop_row(r, idx, **over):
        f = {"origin_id": f"POP{idx:06d}", "origin_household_id": r["true_household_id"], "doc_type": r["doc_type"],
             "doc_number": r["doc_number"], "first_names": r["first_names"], "last_names": r["last_names"],
             "birth_date": r["birth_date"], "locality": r["locality"], "address": r["address"],
             "sisben_group": r["group"], "sisben_subgroup": r["sub"], "survey_date": "2025-06-15"}
        f.update(over)
        return f

    def truth_rec(source, f, r, defects, quarantine):
        ground_truth.append({"source": source, "origin_id": f["origin_id"], "true_person_id": r["true_person_id"],
                       "true_household_id": r["true_household_id"], "defects": "|".join(defects),
                       "goes_to_quarantine": int(quarantine), "true_status": r["status"]})

    k = 0
    for r in true_people:
        k += 1
        defects, over, quarantine = [], {}, False
        x = rng2.random()
        if x < rates["malformed_doc"]:
            over["doc_number"] = r["doc_number"][:3] + "A" + r["doc_number"][4:]
            defects, quarantine = ["malformed_doc"], True
        elif x < rates["malformed_doc"] + rates["invalid_date_or_locality"]:
            if rng2.random() < 0.5:
                over["birth_date"] = "2099-01-01"
            else:
                over["locality"] = "77"
            defects, quarantine = ["invalid_date_or_locality"], True
        f = pop_row(r, k, **over)
        pop.append(f)
        truth_rec("population", f, r, defects, quarantine)
        if quarantine:
            continue
        y = rng2.random()
        if y < rates["exact_duplicate"]:
            k += 1
            d = {**f, "origin_id": f"POP{k:06d}"}
            pop.append(d)
            truth_rec("population", d, r, ["exact_duplicate"], False)
        elif y < rates["exact_duplicate"] + rates["name_variant"]:
            k += 1
            d = {**f, "origin_id": f"POP{k:06d}", "first_names": _variant(rng2, r["first_names"])}
            pop.append(d)
            truth_rec("population", d, r, ["name_variant"], False)
        elif y < rates["exact_duplicate"] + rates["name_variant"] + rates["homonym"]:
            k += 1  # misma identidad aparente (nombre), OTRA persona (otro documento)
            other = {**r, "true_person_id": r["true_person_id"] + "H", "true_household_id": r["true_household_id"] + "H",
                    "doc_number": f"99{rng2.randrange(10**7, 10**8)}",
                    "birth_date": f"{rng2.randrange(1950, 2008)}-{rng2.randrange(1, 13):02d}-{rng2.randrange(1, 29):02d}"}
            d = pop_row(other, k, origin_household_id=other["true_household_id"])
            pop.append(d)
            truth_rec("population", d, other, ["homonym"], False)

    # ---- fuente de validación (supervivencia) ----
    for j, r in enumerate(true_people, 1):
        if rng2.random() < rates["not_found_in_validation"]:
            continue
        v = {"origin_id": f"VAL{j:06d}", "doc_type": r["doc_type"], "doc_number": r["doc_number"],
             "first_names": r["first_names"], "last_names": r["last_names"], "status": r["status"], "cutoff_date": cutoff_date}
        val.append(v)
        truth_rec("validation", v, r, [], False)

    return {"population": pop, "validation": val, "ground_truth": ground_truth, "cutoff_date": cutoff_date}


def write(data, output, cutoff):
    output = Path(output)
    for sub, fields, key in (("landing", POPULATION_FIELDS, "population"), ("landing", VALIDATION_FIELDS, "validation"),
                               ("ground_truth", GROUND_TRUTH_FIELDS, "ground_truth")):
        folder = output / sub / f"cutoff{cutoff}"
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / f"{key}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data[key])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--cutoff", type=int, choices=(1, 2), default=1)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--output", default="data")
    a = ap.parse_args()
    d = generate(a.n, a.cutoff, a.seed)
    write(d, a.output, a.cutoff)
    print(f"population={len(d['population'])} validation={len(d['validation'])} -> {a.output}")
