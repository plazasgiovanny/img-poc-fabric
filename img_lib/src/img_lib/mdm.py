"""MDM sobre Plata (§16): maestro de personas y de hogares, cada uno con clave propia,
con reglas de COINCIDENCIA y de SUPERVIVENCIA.

Reglas por defecto, ILUSTRATIVAS hasta confirmar con el equipo (PENDIENTE G6):
- coincidencia: igualdad exacta de (tipo_doc, num_doc) normalizados; nombres y fecha de
  nacimiento solo actúan como desempate (si la misma llave documental trae fecha de nacimiento
  distinta, se trata como colisión y NO se unen).
- supervivencia: para cada atributo prevalece la fuente de mayor prioridad que lo reporte."""
from collections import defaultdict

PRIORIDAD_FUENTES = ["poblacional", "validacion"]  # ILUSTRATIVO: la poblacional prevalece
ATRIBUTOS = ("nombres", "apellidos", "fecha_nacimiento", "localidad", "direccion", "id_hogar_origen")


def clave_match(reg: dict):
    return (reg["tipo_doc"], reg["num_doc"])


def construir_maestro(registros: list[dict], prioridad=PRIORIDAD_FUENTES):
    """`registros`: dicts de Plata con `fuente` e `id_origen`. Devuelve
    (personas, xref): `personas` = lista del maestro con fuente_ganadora por atributo;
    `xref` = (fuente, id_origen) -> id_persona."""
    grupos = defaultdict(list)
    for r in registros:
        grupos[clave_match(r)].append(r)

    personas, xref, n = [], [], 0
    orden = {f: i for i, f in enumerate(prioridad)}
    for llave in sorted(grupos):
        # desempate: misma llave documental con fecha de nacimiento distinta => colisión
        subgrupos = defaultdict(list)
        for r in grupos[llave]:
            subgrupos[r.get("fecha_nacimiento")].append(r)
        if len(subgrupos) > 1:
            fechas = [f for f in subgrupos if f]
            if len(fechas) > 1:
                partes = [subgrupos[f] for f in sorted(fechas)] + (
                    [subgrupos[None]] if None in subgrupos else [])
            else:
                partes = [sum(subgrupos.values(), [])]
        else:
            partes = [grupos[llave]]
        for parte in partes:
            n += 1
            id_persona = f"P{n:07d}"
            parte = sorted(parte, key=lambda r: orden.get(r["fuente"], 99))
            maestro = {"id_persona": id_persona, "tipo_doc": llave[0], "num_doc": llave[1]}
            ganadora = {}
            for a in ATRIBUTOS:
                for r in parte:
                    if r.get(a) not in (None, ""):
                        maestro[a] = r[a]
                        ganadora[a] = r["fuente"]
                        break
            maestro["fuente_ganadora_por_atributo"] = ganadora
            maestro["n_registros_origen"] = len(parte)
            personas.append(maestro)
            for r in parte:
                xref.append({"fuente": r["fuente"], "id_origen": r["id_origen"],
                             "id_persona": id_persona, "regla_match": "documento_exacto"})
    return personas, xref


def construir_hogares(personas: list[dict]):
    """Maestro de hogares a partir de `id_hogar_origen` (ILUSTRATIVO: el agrupamiento real
    del hogar depende del diccionario de la fuente poblacional, PENDIENTE G2)."""
    hogares, asign = {}, {}
    for p in personas:
        h = p.get("id_hogar_origen") or f"SIN_HOGAR_{p['id_persona']}"
        if h not in hogares:
            hogares[h] = {"id_hogar": f"H{len(hogares) + 1:07d}", "id_hogar_origen": h, "miembros": 0}
        hogares[h]["miembros"] += 1
        asign[p["id_persona"]] = hogares[h]["id_hogar"]
    return list(hogares.values()), asign
