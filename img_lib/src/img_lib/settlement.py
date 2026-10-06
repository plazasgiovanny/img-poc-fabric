"""Etapa 3 (§18, Tabla 8): cuadernos de liquidación como funciones puras sobre la base de cruces.

Los criterios y reglas son DATOS (tablas param.*), no código. Motor genérico con los operadores
=, !=, IN y NOT IN. `is_illustrative = 1` en param.* marca solo valores de demostración (fuentes de
financiación, partición de listados, prioridad de operadores)."""
import csv
import io
import os
from collections import defaultdict

from . import dispersal, mapping
from .fingerprint import sha256_bytes
from .params import has_illustrative

# Nombre de campo usado en param.* -> columna de la base de cruces (Tabla 7)
FIELD_ALIASES = {"validation_status": "validation_value"}


def _matches(row, field, operator, value):
    current_value = row.get(FIELD_ALIASES.get(field, field))
    current_value = None if current_value is None else str(current_value)
    values = {v.strip() for v in str(value).split(",")}
    if operator == "=":
        return current_value == str(value)
    if operator == "!=":
        return current_value != str(value)
    if operator == "IN":
        return current_value in values
    if operator == "NOT IN":  # como en SQL, un valor nulo no cumple «NOT IN» (no bloquea)
        return current_value is not None and current_value not in values
    raise ValueError(f"unsupported operator: {operator}")


# nb_00_targeting: elegibles y excluidos, cada exclusión con su causal
def target(base, criteria, block_rules):
    res = []
    for r in base:
        reasons = [f"NOT_MET_{c['criterion']}" for c in criteria
                    if not _matches(r, c["field"], c["operator"], c["value"])]
        reasons += [b["reason"] for b in block_rules
                     if _matches(r, b["field"], b["operator"], b["value"])]
        res.append({"cycle_id": r["cycle_id"], "person_id": r["person_id"], "household_id": r["household_id"],
                    "eligible": not reasons, "reasons": ";".join(reasons) or None})
    return res


# nb_01_holder: un titular por hogar. Criterios (param.holder_rule, en orden): REQUIRED filtra
# (mayor de edad, elegible = focalizada y no bloqueada); ASC/DESC ordena (mujer, bancarizada, mayor edad, número de documento).
def _derived(member, eligible, criterion):
    if criterion == "is_adult":
        age = member.get("age")
        return int(age is not None and int(age) >= mapping.ADULT_AGE)
    if criterion == "is_eligible":  # elegible = cumple focalización (grupo SISBEN A) y no tiene causal de bloqueo
        return int(eligible)
    if criterion == "is_woman":
        return int(str(member.get("sex")) == mapping.SEX_WOMAN)
    if criterion == "is_banked":
        return int(str(member.get("banked")) == "1")
    value = member.get(criterion)
    if criterion == "doc_number" and value is not None:  # numérico si se puede ("99999" antes que "100000")
        number = mapping.to_int(value)
        return (0, number) if number is not None else (1, str(value))
    return int(value) if criterion == "age" and value is not None else value


def _sort_key(value, descending):
    # los nulos van siempre al final
    return (value is not None, value) if descending else (value is None, 0 if value is None else value)


def households_without_holder(targeting, holders) -> int:
    """Hogares con al menos una persona elegible pero sin titular (ninguna elegible es adulta)."""
    with_holder = {t["household_id"] for t in holders}
    return len({f["household_id"] for f in targeting if f["eligible"]} - with_holder)


def select_holder(targeting, base, holder_rule):
    by_person = {r["person_id"]: r for r in base}
    eligible_of = {f["person_id"]: f["eligible"] for f in targeting}
    household_members = defaultdict(list)
    for f in targeting:
        household_members[f["household_id"]].append(by_person[f["person_id"]])
    rank = sorted(holder_rule, key=lambda x: x["rank"])
    holders = []
    for household in sorted(household_members):
        members = household_members[household]
        for c in rank:
            if c["sort_direction"] == "REQUIRED":
                members = [m for m in members if _derived(m, eligible_of[m["person_id"]], c["criterion"])]
        if not members:
            continue  # hogar sin titular elegible
        members = sorted(members, key=lambda m: m["person_id"])  # último desempate, determinista
        for c in reversed(rank):  # orden estable: el primer criterio manda
            if c["sort_direction"] == "REQUIRED":
                continue
            descending = c["sort_direction"] == "DESC"
            members = sorted(members, reverse=descending, key=lambda m, c=c, d=descending: _sort_key(
                _derived(m, eligible_of[m["person_id"]], c["criterion"]), d))
        t = members[0]
        holders.append({"cycle_id": t["cycle_id"], "household_id": household, "person_id": t["person_id"],
                          "n_candidates": len(members)})
    return holders


# nb_02_payment_method: el operador es el de la cuenta de la titular (Cuenta1). Si no tiene operador activo
# (SIN OPERADOR o fuera de param.operators) se asigna el de mayor prioridad como respaldo.
def assign_payment_method(holders, operators, base):
    ops = sorted(operators, key=lambda o: o["priority"])
    if not ops:
        raise ValueError("no enabled active operators")
    enabled = {o["operator"] for o in ops}
    by_person = {r["person_id"]: r for r in base}
    res = []
    for t in holders:
        own = (by_person[t["person_id"]].get("operator") or "").upper()
        if own in enabled:
            res.append({**t, "operator": own, "mode": "account_operator"})
        else:
            res.append({**t, "operator": ops[0]["operator"], "mode": "fallback_operator"})
    return res


# nb_03_amount: monto base por hogar desde param.amounts (parametrizable; 120000 según el diccionario de dispersión)
def calculate_amount(holders, amounts):
    base = next(m for m in amounts if m["concept"] == "BASE_HOUSEHOLD_AMOUNT")["amount"]
    return [{"cycle_id": t["cycle_id"], "household_id": t["household_id"], "person_id": t["person_id"],
             "amount": float(base), "components": f"BASE_HOUSEHOLD_AMOUNT={base}"} for t in holders]


# nb_04_funding_source: asigna la fuente con saldo y marca si se excede el techo (insumo del Control 3)
def assign_funding_source(amounts, sources):
    balance = {f["funding_source"]: float(f["ceiling"]) for f in sources}
    rank = [f["funding_source"] for f in sources]
    payments, over_ceiling = [], 0
    for m in amounts:
        source = next((f for f in rank if balance[f] >= m["amount"]), rank[-1])
        if balance[source] < m["amount"]:
            over_ceiling += 1
        balance[source] -= m["amount"]
        payments.append({**m, "funding_source": source})
    return payments, {"balance": balance, "payments_over_ceiling": over_ceiling}


# nb_05_payment_lists: sábana del ciclo (una fila por pago, con `seq`) y un archivo por operador (sdp_operador)
def generate_payment_lists(payments, payment_method, base):
    by_person = {r["person_id"]: r for r in base}
    method = {m["household_id"]: m for m in payment_method}
    rows = []
    for p in payments:
        b = by_person[p["person_id"]]
        account_operator = method[p["household_id"]]["operator"]
        operator, product = mapping.operator_to_dispersal(account_operator)
        rows.append({
            "cycle_id": p["cycle_id"], "seq": 0, "operator": operator or mapping.NO_OPERATOR, "product": product,
            "account_operator": account_operator, "funding_source": p["funding_source"],
            "household_id": p["household_id"], "person_id": p["person_id"], "origin_id": b.get("origin_id"),
            "doc_type": b["doc_type"], "doc_number": b["doc_number"], "first_name": b.get("first_name"),
            "second_name": b.get("second_name"), "last_name": b.get("last_name"),
            "second_last_name": b.get("second_last_name"), "renec_validity": b.get("renec_validity"),
            "age": b.get("age"), "sex": b.get("sex"), "locality": b.get("locality"),
            "locality_name": b.get("locality_name"), "amount": p["amount"]})
    master_sheet = sorted(rows, key=lambda f: (f["operator"], f["funding_source"], f["household_id"]))
    by_file = defaultdict(list)
    for n, f in enumerate(master_sheet, 1):
        f["seq"] = n
        by_file[f["operator"]].append(f)
    return master_sheet, dict(by_file)


def _csv_bytes(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def publish(files, root, cycle_id):
    """nb_07_publish (adaptación de la PoC al §18.4): escribe {raiz}/{cycle_id}/{operador}/payment_list_<operador>.xlsx
    (32 columnas del diccionario de dispersión) y un manifiesto SHA-256. En producción el destino es Azure Storage
    con política de inmutabilidad; aquí es OneLake Files (sin inmutabilidad). Devuelve el manifiesto."""
    manifest = []
    for operator, rows in sorted(files.items()):
        folder = os.path.join(root, cycle_id, operator)
        os.makedirs(folder, exist_ok=True)
        data = dispersal.xlsx_bytes([dispersal.to_dispersal_row(r) for r in rows])
        name = f"payment_list_{operator}.xlsx"
        with open(os.path.join(folder, name), "wb") as f:
            f.write(data)
        manifest.append({"file": f"{operator}/{name}", "rows": len(rows), "sha256": sha256_bytes(data)})
    with open(os.path.join(root, cycle_id, "manifest_sha256.csv"), "wb") as f:
        f.write(_csv_bytes(manifest))
    return manifest


# nb_06_report: contenido mínimo del §18.4
def build_report(*, cycle_id, cutoff_date, source_versions, applied_params, notebook_versions,
                  base, targeting, holders, payments, master_sheet, approvals):
    exclusions = defaultdict(int)
    for f in targeting:
        for c in (f["reasons"] or "").split(";"):
            if c:
                exclusions[c] += 1
    total_payments = sum(p["amount"] for p in payments)
    total_lists = sum(f["amount"] for f in master_sheet)
    totals = defaultdict(float)
    for f in master_sheet:
        totals[("operator", f["operator"])] += f["amount"]
        totals[("source", f["funding_source"])] += f["amount"]
    applied = [p for items in applied_params.values() for p in items]
    return {
        "cycle_id": cycle_id, "cutoff_date": cutoff_date, "source_versions": source_versions,
        "applied_params": {k: len(v) for k, v in applied_params.items()},
        "uses_illustrative_params": has_illustrative(applied),
        "notebook_versions": notebook_versions,
        "counts": {"universe": len(base), "eligible": sum(1 for f in targeting if f["eligible"]),
                    "holders": len(holders), "settled_payments": len(payments),
                    "households_without_holder": households_without_holder(targeting, holders)},
        "exclusions_by_reason": dict(exclusions),
        "totals_by_operator": {k[1]: v for k, v in totals.items() if k[0] == "operator"},
        "totals_by_source": {k[1]: v for k, v in totals.items() if k[0] == "source"},
        "lists_sum_equals_settlement": abs(total_payments - total_lists) < 1e-6,
        "approvals": approvals,
    }
