"""Etapa 2 (§17): base de cruces. Una fila por persona y por ciclo; registra HECHOS, no decisiones.
Campos de referencia de la Tabla 7 adaptados al esquema de la base maestra (ver docs/NAMING.md).

Universo = personas con registro en la fuente poblacional (§17: las poblacionales definen el
universo). La fuente de validación es la base de inhumados: «encontrado» = existe una fila con el mismo
tipo y número de documento."""


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
            "first_name": p.get("first_name"), "second_name": p.get("second_name"),
            "last_name": p.get("last_name"), "second_last_name": p.get("second_last_name"),
            "first_names": p.get("first_names"), "last_names": p.get("last_names"),
            "birth_date": p.get("birth_date"), "sex": p.get("sex"), "age": p.get("age"),
            # Hogar y ubicación
            "household_id": p["household_id"], "household_role": p.get("household_role"),
            "locality": p.get("locality"), "locality_name": p.get("locality_name"),
            # Clasificación socioeconómica y vigencia de la cédula (RENEC)
            "sisben_group": p.get("sisben_group"), "renec_validity": p.get("renec_validity"),
            # Marcas de validación (inhumados): encontrado (sí/no), valor reportado y fecha de defunción
            "validation_found": "YES" if v else "NO",
            "validation_value": "DECEASED" if v else None,
            "validation_cutoff_date": cutoff_date if v else None,
            "death_date": v.get("death_date") if v else None,
            # Datos financieros: operador de pago de la maestra (Cuenta1) y bancarización
            "operator": p.get("operator"), "banked": p.get("banked"), "product_type": None, "product_status": None,
            # Trazabilidad
            "execution_id": execution_id, "notebook_version": notebook_version, "process_ts": ts,
        })
    return base


def match_pct(base):
    """Insumo del Control 2: % de personas del universo que existen en la base de inhumados."""
    if not base:
        return 0.0
    return 100.0 * sum(1 for r in base if r["validation_found"] == "YES") / len(base)
