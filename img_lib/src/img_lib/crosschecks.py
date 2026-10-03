"""Etapa 2 (§17): base de cruces. Una fila por persona y por ciclo; registra HECHOS, no decisiones.
Campos de referencia de la Tabla 7 (el documento advierte que los nombres deben ajustarse contra
las variables del manual vigente).

Universo = personas con registro en la fuente poblacional (§17: las poblacionales definen el
universo). Campos sin fuente en la PoC (rol en el hogar, datos financieros) quedan en None: no se
inventan (PENDIENTE G2)."""


def first_per_person(rows):
    first_rows = {}
    for f in sorted(rows, key=lambda r: r["origin_id"]):
        first_rows.setdefault(f["person_id"], f)
    return first_rows


def build_base(pop_gold, val_gold, *, cycle_id, cutoff_date, source_versions, execution_id,
                   notebook_version, ts):
    """`pop_gold` / `val_gold`: filas de lh_gold.sources.*_cutoff (con person_id e household_id).
    `source_versions`: {"population": ..., "validation": ...}. Devuelve filas de crosschecks.crosscheck_base."""
    pop = first_per_person(pop_gold)
    val = first_per_person(val_gold)
    base = []
    for person_id in sorted(pop):
        p, v = pop[person_id], val.get(person_id)
        base.append({
            # Ciclo
            "cycle_id": cycle_id, "cutoff_date": cutoff_date,
            "population_source_version": source_versions.get("population"),
            "validation_source_version": source_versions.get("validation"),
            # Persona
            "person_id": person_id, "doc_type": p["doc_type"], "doc_number": p["doc_number"],
            "first_names": p["first_names"], "last_names": p["last_names"], "birth_date": p["birth_date"],
            # Hogar y ubicación (household_role: sin fuente definida en la PoC)
            "household_id": p["household_id"], "household_role": None, "locality": p["locality"],
            "address": p.get("address"),
            # Clasificación socioeconómica
            "sisben_group": p.get("sisben_group"), "sisben_subgroup": p.get("sisben_subgroup"),
            "survey_date": p.get("survey_date"),
            # Marcas de validación: encontrado (sí/no), valor reportado y fecha de corte
            "validation_found": "YES" if v else "NO",
            "validation_value": v["status"] if v else None,
            "validation_cutoff_date": v["cutoff_date"] if v else None,
            # Datos financieros: sin fuente financiera en la PoC
            "operator": None, "product_type": None, "product_status": None,
            # Trazabilidad
            "execution_id": execution_id, "notebook_version": notebook_version, "process_ts": ts,
        })
    return base


def match_pct(base):
    """Insumo del Control 2: % de personas del universo encontradas en la fuente de validación."""
    if not base:
        return 0.0
    return 100.0 * sum(1 for r in base if r["validation_found"] == "YES") / len(base)
