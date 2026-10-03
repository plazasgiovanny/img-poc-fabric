"""MDM sobre Plata (§16): maestro de personas y de hogares, cada uno con clave propia,
con reglas de COINCIDENCIA y de SUPERVIVENCIA.

Reglas por defecto, ILUSTRATIVAS hasta confirmar con el equipo (PENDIENTE G6):
- coincidencia: igualdad exacta de (doc_type, doc_number) normalizados; nombres y fecha de
  nacimiento solo actúan como desempate (si la misma llave documental trae fecha de nacimiento
  distinta, se trata como colisión y NO se unen).
- supervivencia: para cada atributo prevalece la fuente de mayor prioridad que lo reporte."""
from collections import defaultdict

SOURCE_PRIORITY = ["population", "validation"]  # ILUSTRATIVO: la poblacional prevalece
ATTRIBUTES = ("first_names", "last_names", "birth_date", "locality", "address", "origin_household_id")


def match_key(rec: dict):
    return (rec["doc_type"], rec["doc_number"])


def build_master(records: list[dict], priority=SOURCE_PRIORITY):
    """`records`: dicts de Plata con `source` e `origin_id`. Devuelve
    (personas, xref): `people` = lista del maestro con source_winner por atributo;
    `xref` = (fuente, origin_id) -> person_id."""
    groups = defaultdict(list)
    for r in records:
        groups[match_key(r)].append(r)

    people, xref, n = [], [], 0
    rank = {f: i for i, f in enumerate(priority)}
    for key in sorted(groups):
        # desempate: misma llave documental con fecha de nacimiento distinta => colisión
        subgroups = defaultdict(list)
        for r in groups[key]:
            subgroups[r.get("birth_date")].append(r)
        if len(subgroups) > 1:
            dates = [f for f in subgroups if f]
            if len(dates) > 1:
                parts = [subgroups[f] for f in sorted(dates)] + (
                    [subgroups[None]] if None in subgroups else [])
            else:
                parts = [sum(subgroups.values(), [])]
        else:
            parts = [groups[key]]
        for part in parts:
            n += 1
            person_id = f"P{n:07d}"
            part = sorted(part, key=lambda r: rank.get(r["source"], 99))
            master = {"person_id": person_id, "doc_type": key[0], "doc_number": key[1]}
            winner = {}
            for a in ATTRIBUTES:
                for r in part:
                    if r.get(a) not in (None, ""):
                        master[a] = r[a]
                        winner[a] = r["source"]
                        break
            master["winning_source_by_attribute"] = winner
            master["n_origin_records"] = len(part)
            people.append(master)
            for r in part:
                xref.append({"source": r["source"], "origin_id": r["origin_id"],
                             "person_id": person_id, "match_rule": "exact_document"})
    return people, xref


def build_households(people: list[dict]):
    """Maestro de hogares a partir de `origin_household_id` (ILUSTRATIVO: el agrupamiento real
    del hogar depende del diccionario de la fuente poblacional, PENDIENTE G2)."""
    households, assign = {}, {}
    for p in people:
        h = p.get("origin_household_id") or f"NO_HOUSEHOLD_{p['person_id']}"
        if h not in households:
            households[h] = {"household_id": f"H{len(households) + 1:07d}", "origin_household_id": h, "members": 0}
        households[h]["members"] += 1
        assign[p["person_id"]] = households[h]["household_id"]
    return list(households.values()), assign
