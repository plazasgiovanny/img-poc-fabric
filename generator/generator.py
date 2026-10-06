"""Generador de datos SINTÉTICOS para la PoC IMG (Ley 1581 de 2012: no hay datos personales reales).

- Determinista: misma semilla => mismos datos. Los datos NO se versionan (ver .gitignore).
- Documentos en rango imposible (prefijo 99 + 8 dígitos) para no chocar con personas reales.
- Emite la base maestra poblacional con los nombres reales (RSH_*, SIS_*, Cuenta1) separada por '||'
  (population.csv) y la base de inhumados (validation.csv: tipo, número y fecha de defunción).
- Inyecta defectos controlados y escribe la "verdad conocida" para medir errores (<1 %, §7 Exp. 2):
  documentos inválidos, fechas/localidades inválidas, duplicados, homónimos, bloqueados por RENEC,
  inhumados, menores de edad, hogares sin mujer adulta y hogares sin titular elegible.

Formato de los CSV: UTF-8, separador '||', fechas ISO yyyy-mm-dd, sin comillas, con encabezado.

Uso local:  python generator.py --n 500 --cutoff 1 --output data/
En Fabric: subir lh_control/Files/synthetic/{landing,ground_truth}."""
import argparse
import csv
import random
from datetime import date
from pathlib import Path

SEP = "||"
SEED = 20261002
RATES = {  # parametrizables
    "exact_duplicate": 0.02, "name_variant": 0.02, "homonym": 0.01, "malformed_doc": 0.015,
    "invalid_doc_type": 0.005, "invalid_date_or_locality": 0.01, "deceased": 0.03,
    "doc_type_mismatch_in_registry": 0.15, "extra_registry_rows": 0.02, "cutoff2_change": 0.03,
    "renec_blocked": 0.05, "renec_12": 0.01, "renec_null": 0.02, "banked": 0.55, "no_locality": 0.02,
}
FIRST_NAMES = ["María", "José", "Luz", "Carlos", "Ana", "Juan", "Sandra", "Luis", "Marta", "Pedro",
           "Diana", "Jorge", "Paola", "Andrés", "Rosa", "Camilo", "Nelly", "Fabián", "Yolanda", "Iván"]
LAST_NAMES = ["Rodríguez", "Gómez", "Martínez", "López", "Pérez", "Ramírez", "Torres", "Castro",
             "Rojas", "Moreno", "Díaz", "Vargas", "Muñoz", "Ortiz", "Cárdenas", "Peña", "Suárez"]
GROUPS = ["1. SISBEN IV - A", "2. SISBEN IV - B", "3. SISBEN IV - C", "4. SISBEN IV - D"]
GROUP_WEIGHTS = [0.40, 0.25, 0.20, 0.15]
OPERATORS = ["DAVIPLATA", "NEQUI", "ALM", "MOVII", "EFECTY", "DALE", "POWWI"]
RENEC_BLOCKING = [21, 22, 23, 24, 25, 53]
LOCALITY_NAMES = {
    1: "USAQUEN", 2: "CHAPINERO", 3: "SANTA FE", 4: "SAN CRISTOBAL", 5: "USME", 6: "TUNJUELITO", 7: "BOSA",
    8: "KENNEDY", 9: "FONTIBON", 10: "ENGATIVA", 11: "SUBA", 12: "BARRIOS UNIDOS", 13: "TEUSAQUILLO",
    14: "MARTIRES", 15: "ANTONIO NARIÑO", 16: "PUENTE ARANDA", 17: "LA CANDELARIA", 18: "RAFAEL URIBE URIBE",
    19: "CIUDAD BOLIVAR", 20: "SUMAPAZ", 999: "ZZ-SIN INFORMACION",
}

POPULATION_FIELDS = [
    "RSH_id_llave_maestra", "RSH_id_hogar", "RSH_tip_parentesco", "RSH_tip_documento", "RSH_num_documento",
    "RSH_pri_nombre", "RSH_seg_nombre", "RSH_pri_apellido", "RSH_seg_apellido", "RSH_sexo_persona",
    "RSH_fec_nacimiento", "RSH_grupo_S4", "RSH_vigencia_renec", "SIS_edad", "SIS_cod_loc", "SIS_nom_loc",
    "SIS_bancarizado", "Cuenta1",
]
VALIDATION_FIELDS = ["RSH_tip_documento", "RSH_num_documento", "fecha_defuncion"]
GROUND_TRUTH_FIELDS = ["source", "origin_id", "true_person_id", "true_household_id", "defects",
                 "goes_to_quarantine", "true_status", "true_renec_blocked", "true_is_holder"]


def _age(birth, ref):
    return ref.year - birth.year - ((ref.month, ref.day) < (birth.month, birth.day))


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


def _birth(rng, age):
    """Fecha de nacimiento para una edad aproximada al 30-sep-2026 (día <= 28)."""
    d = date(2026 - age - rng.randrange(0, 2), rng.randrange(1, 13), rng.randrange(1, 29))
    return d if d <= date(2026, 9, 1) else date(d.year - 1, d.month, d.day)


def _doc_type(rng, age):
    if age < 7:
        return 4  # registro civil
    if age < 18:
        return 2  # tarjeta de identidad
    x = rng.random()
    return 1 if x < 0.94 else 3 if x < 0.98 else 9


def _renec(rng, rates):
    x = rng.random()
    if x < rates["renec_null"]:
        return None
    if x < rates["renec_null"] + rates["renec_12"]:
        return 12
    if x < rates["renec_null"] + rates["renec_12"] + rates["renec_blocked"]:
        return rng.choice(RENEC_BLOCKING)
    return 0


def _people(rng, n_people, rates):
    """Población real (verdad): hogares con jefe, cónyuge, hijos (menores y mayores) y otros parientes."""
    people, h = [], 0
    while len(people) < n_people:
        h += 1
        group = rng.choices(GROUPS, GROUP_WEIGHTS)[0]
        loc = 999 if rng.random() < rates["no_locality"] else rng.randrange(1, 21)
        head_age = rng.randrange(19, 81)
        head_sex = rng.choice((1, 2))
        members = [(1, head_age, head_sex)]
        if rng.random() < 0.55:
            members.append((2, max(18, head_age + rng.randrange(-8, 9)), 3 - head_sex))
        for _ in range(rng.choice((0, 0, 1, 1, 2, 3))):
            child_age = rng.randrange(0, 18) if rng.random() < 0.7 else rng.randrange(18, 36)
            members.append((3, min(child_age, max(0, head_age - 16)), rng.choice((1, 2))))
        if rng.random() < 0.08:
            members.append((rng.choice((4, 5, 6, 14, 19)), rng.randrange(18, 85), rng.choice((1, 2))))
        for role, age, sex in members:
            if len(people) >= n_people:
                break
            adult = age >= 18
            banked = adult and rng.random() < rates["banked"]
            people.append({
                "true_person_id": f"R{len(people) + 1:06d}", "true_household_id": f"HR{h:05d}",
                "role": role, "doc_type": _doc_type(rng, age), "doc_number": f"99{rng.randrange(10**7, 10**8)}",
                "first_name": rng.choice(FIRST_NAMES),
                "second_name": rng.choice(FIRST_NAMES) if rng.random() < 0.5 else "",
                "last_name": rng.choice(LAST_NAMES),
                "second_last_name": rng.choice(LAST_NAMES) if rng.random() < 0.9 else "",
                "sex": sex, "birth_date": _birth(rng, age), "group": group, "locality": loc,
                "renec": _renec(rng, rates), "operator": rng.choice(OPERATORS) if banked else "SIN OPERADOR",
                "banked": int(banked), "status": "DECEASED" if rng.random() < rates["deceased"] else "ALIVE",
                "in_registry": False,
            })
    return people


def generate(n_people=500, cutoff=1, seed=SEED, rates=None):
    rates = {**RATES, **(rates or {})}
    rng = random.Random(seed)  # la base de personas es idéntica en cortes 1 y 2
    cutoff_date = "2026-09-30" if cutoff == 1 else "2026-10-31"
    cutoff_day = date.fromisoformat(cutoff_date)
    true_people = _people(rng, n_people, rates)
    seen = set()
    for r in true_people:  # evita colisiones accidentales de documento
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
                r["locality"] = rng2.randrange(1, 21)

    pop, val, ground_truth = [], [], []

    def pop_row(r, idx, **over):
        f = {"RSH_id_llave_maestra": f"7{idx:07d}", "RSH_id_hogar": r["true_household_id"],
             "RSH_tip_parentesco": r["role"], "RSH_tip_documento": r["doc_type"],
             "RSH_num_documento": r["doc_number"], "RSH_pri_nombre": r["first_name"],
             "RSH_seg_nombre": r["second_name"], "RSH_pri_apellido": r["last_name"],
             "RSH_seg_apellido": r["second_last_name"], "RSH_sexo_persona": r["sex"],
             "RSH_fec_nacimiento": r["birth_date"].isoformat(), "RSH_grupo_S4": r["group"],
             "RSH_vigencia_renec": "" if r["renec"] is None else r["renec"],
             "SIS_edad": _age(r["birth_date"], cutoff_day), "SIS_cod_loc": r["locality"],
             "SIS_nom_loc": LOCALITY_NAMES[r["locality"]], "SIS_bancarizado": r["banked"],
             "Cuenta1": r["operator"]}
        f.update(over)
        return f

    rows_by_person = {}  # true_person_id -> (persona, ¿su fila entra a Plata?)

    def truth_rec(source, origin_id, r, defects, quarantine, household=None):
        ground_truth.append({
            "source": source, "origin_id": origin_id, "true_person_id": r["true_person_id"],
            "true_household_id": r["true_household_id"] if household is None else household,
            "defects": "|".join(defects), "goes_to_quarantine": int(quarantine), "true_status": r["status"],
            "true_renec_blocked": int(source == "population" and r["renec"] not in (None, 0, 12)),
            "true_is_holder": 0})

    k = 0
    p_dup = rates["exact_duplicate"]
    p_var = p_dup + rates["name_variant"]
    p_hom = p_var + rates["homonym"]
    t1 = rates["malformed_doc"]
    t2 = t1 + rates["invalid_doc_type"]
    t3 = t2 + rates["invalid_date_or_locality"]
    for r in true_people:
        k += 1
        defects, over, quarantine = [], {}, False
        x = rng2.random()
        if x < t1:
            over["RSH_num_documento"] = r["doc_number"][:3] + "A" + r["doc_number"][4:]
            defects, quarantine = ["malformed_doc"], True
        elif x < t2:
            over["RSH_tip_documento"] = 0  # «No tiene»: no identifica a la persona
            defects, quarantine = ["invalid_doc_type"], True
        elif x < t3:
            if rng2.random() < 0.5:
                over["RSH_fec_nacimiento"] = "2099-01-01"
            else:
                over["SIS_cod_loc"], over["SIS_nom_loc"] = 77, "SIN CATALOGO"
            defects, quarantine = ["invalid_date_or_locality"], True
        f = pop_row(r, k, **over)
        pop.append(f)
        truth_rec("population", f["RSH_id_llave_maestra"], r, defects, quarantine)
        if quarantine:
            continue
        rows_by_person[r["true_person_id"]] = r
        y = rng2.random()
        if y < p_dup:
            k += 1
            d = {**f, "RSH_id_llave_maestra": f"7{k:07d}"}
            pop.append(d)
            truth_rec("population", d["RSH_id_llave_maestra"], r, ["exact_duplicate"], False)
        elif y < p_var:
            k += 1
            d = {**f, "RSH_id_llave_maestra": f"7{k:07d}", "RSH_pri_nombre": _variant(rng2, r["first_name"])}
            pop.append(d)
            truth_rec("population", d["RSH_id_llave_maestra"], r, ["name_variant"], False)
        elif y < p_hom:
            k += 1  # misma identidad aparente (nombre), OTRA persona (otro documento)
            other = {**r, "true_person_id": r["true_person_id"] + "H",
                     "true_household_id": r["true_household_id"] + "H", "role": 1,
                     "doc_number": f"99{rng2.randrange(10**7, 10**8)}", "in_registry": False,
                     "birth_date": _birth(rng2, max(18, _age(r["birth_date"], cutoff_day)))}
            while other["doc_number"] in seen:
                other["doc_number"] = f"99{rng2.randrange(10**7, 10**8)}"
            seen.add(other["doc_number"])
            d = pop_row(other, k, RSH_id_hogar=other["true_household_id"],
                        RSH_tip_documento=_doc_type(rng2, 30) if other["doc_type"] in (2, 4) else other["doc_type"])
            other["doc_type"] = d["RSH_tip_documento"]
            pop.append(d)
            truth_rec("population", d["RSH_id_llave_maestra"], other, ["homonym"], False)
            rows_by_person[other["true_person_id"]] = other

    # ---- base de inhumados: existe = hay una fila con el mismo tipo y número de documento ----
    def registry_row(r, doc_type, death_day):
        return {"RSH_tip_documento": doc_type, "RSH_num_documento": r["doc_number"],
                "fecha_defuncion": death_day.isoformat()}

    for r in true_people:
        if r["status"] != "DECEASED":
            continue
        death = date.fromordinal(cutoff_day.toordinal() - rng2.randrange(1, 1500 if cutoff == 1 else 400))
        if rng2.random() < rates["doc_type_mismatch_in_registry"]:
            # mismo número, otro tipo: para el cruce por tipo + número es OTRA identidad (no bloquea)
            v = registry_row(r, 1 if r["doc_type"] != 1 else 3, death)
            other = {**r, "true_person_id": r["true_person_id"] + "T"}
            val.append(v)
            truth_rec("validation", f"INH-{v['RSH_tip_documento']}-{v['RSH_num_documento']}", other,
                      ["doc_type_mismatch"], False, household="")
        else:
            v = registry_row(r, r["doc_type"], death)
            val.append(v)
            r["in_registry"] = True
            truth_rec("validation", f"INH-{v['RSH_tip_documento']}-{v['RSH_num_documento']}", r, [], False,
                      household="")
    for j in range(int(n_people * rates["extra_registry_rows"])):  # inhumados que no están en la maestra
        ghost = {"true_person_id": f"X{j + 1:06d}", "true_household_id": "", "doc_number": "",
                 "status": "DECEASED", "renec": None}
        while True:
            ghost["doc_number"] = f"99{rng2.randrange(10**7, 10**8)}"
            if ghost["doc_number"] not in seen:
                break
        seen.add(ghost["doc_number"])
        v = registry_row(ghost, 1, date.fromordinal(cutoff_day.toordinal() - rng2.randrange(1, 1500)))
        val.append(v)
        truth_rec("validation", f"INH-1-{v['RSH_num_documento']}", ghost, [], False, household="")

    # ---- titular esperado por hogar (verdad), calculado de forma independiente del pipeline ----
    by_household = {}
    for r in rows_by_person.values():
        by_household.setdefault(r["true_household_id"], []).append(r)
    expected_holders = set()
    for members in by_household.values():
        eligible = [m for m in members if m["group"] == GROUPS[0] and m["renec"] in (None, 0, 12)
                    and not m["in_registry"] and _age(m["birth_date"], cutoff_day) >= 18]
        if eligible:
            best = min(eligible, key=lambda m: (m["sex"] != 2, not m["banked"],
                                                -_age(m["birth_date"], cutoff_day), m["doc_number"]))
            expected_holders.add(best["true_person_id"])
    for g in ground_truth:
        if g["source"] == "population" and g["true_person_id"] in expected_holders:
            g["true_is_holder"] = 1

    return {"population": pop, "validation": val, "ground_truth": ground_truth, "cutoff_date": cutoff_date}


def write(data, output, cutoff):
    output = Path(output)
    for sub, fields, key in (("landing", POPULATION_FIELDS, "population"), ("landing", VALIDATION_FIELDS, "validation")):
        folder = output / sub / f"cutoff{cutoff}"
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / f"{key}.csv", "w", newline="", encoding="utf-8") as f:
            f.write(SEP.join(fields) + "\n")
            for row in data[key]:
                cells = ["" if row[c] is None else str(row[c]) for c in fields]
                assert not any(SEP in c or "\n" in c for c in cells)
                f.write(SEP.join(cells) + "\n")
    folder = output / "ground_truth" / f"cutoff{cutoff}"
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "ground_truth.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=GROUND_TRUTH_FIELDS)
        w.writeheader()
        w.writerows(data["ground_truth"])


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
