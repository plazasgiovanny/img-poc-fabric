"""Etapa 3 (§18, Tabla 8): cuadernos de liquidación como funciones puras sobre la base de cruces.

Los criterios y reglas son DATOS (tablas param.*), no código. Esta PoC solo implementa el motor
genérico (operadores =, !=, IN) y los pasos mínimos. Lo marcado ILUSTRATIVO no proviene del manual
de la SDIS (PENDIENTES G3 a G7)."""
import csv
import io
from collections import defaultdict

from .fingerprint import sha256_bytes
from .params import has_illustrative

# Nombre de campo usado en param.* -> columna de la base de cruces (Tabla 7)
FIELD_ALIASES = {"validation_status": "validation_value"}


def _matches(row, field, operator, value):
    current_value = row.get(FIELD_ALIASES.get(field, field))
    current_value = None if current_value is None else str(current_value)
    if operator == "=":
        return current_value == str(value)
    if operator == "!=":
        return current_value != str(value)
    if operator == "IN":
        return current_value in {v.strip() for v in str(value).split(",")}
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


# nb_01_holder: un titular por hogar según el orden de criterios parametrizado
def select_holder(targeting, base, holder_rule):
    by_person = {r["person_id"]: r for r in base}
    candidates = defaultdict(list)
    for f in targeting:
        if f["eligible"]:
            candidates[f["household_id"]].append(by_person[f["person_id"]])
    rank = sorted(holder_rule, key=lambda x: x["rank"])
    holders = []
    for household in sorted(candidates):
        members = candidates[household]
        for criterion in reversed(rank):  # orden estable: el primer criterio manda
            members = sorted(members, key=lambda m, c=criterion: str(m.get(c["criterion"]) or ""),
                              reverse=criterion["sort_direction"] == "DESC")
        t = members[0]
        holders.append({"cycle_id": t["cycle_id"], "household_id": household, "person_id": t["person_id"],
                          "n_candidates": len(members)})
    return holders


# nb_02_payment_method: ILUSTRATIVO. Sin datos financieros reales, se asigna el operador habilitado de
# mayor prioridad; si la base trae product_status, solo se asignan productos activos (no definido: G2).
def assign_payment_method(holders, operators):
    ops = sorted(operators, key=lambda o: o["priority"])
    if not ops:
        raise ValueError("no enabled active operators")
    return [{**t, "operator": ops[0]["operator"], "mode": "illustrative_stub"} for t in holders]


# nb_03_amount: ILUSTRATIVO, monto base por hogar desde param.amounts
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


# nb_05_payment_lists: archivos por operador y fuente + sábana del ciclo
def generate_payment_lists(payments, payment_method, base):
    by_person = {r["person_id"]: r for r in base}
    op = {m["household_id"]: m["operator"] for m in payment_method}
    rows = []
    for p in payments:
        b = by_person[p["person_id"]]
        rows.append({"cycle_id": p["cycle_id"], "operator": op[p["household_id"]],
                      "funding_source": p["funding_source"], "household_id": p["household_id"],
                      "person_id": p["person_id"], "doc_type": b["doc_type"], "doc_number": b["doc_number"],
                      "first_names": b["first_names"], "last_names": b["last_names"], "amount": p["amount"]})
    master_sheet = sorted(rows, key=lambda f: (f["operator"], f["funding_source"], f["household_id"]))
    by_file = defaultdict(list)
    for f in master_sheet:
        by_file[(f["operator"], f["funding_source"])].append(f)
    return master_sheet, dict(by_file)


def _csv_bytes(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def publish(files, root, cycle_id):
    """nb_07_publish (adaptación de la PoC al §18.4): escribe {raiz}/{cycle_id}/{operador}/ y un
    manifiesto SHA-256. En producción el destino es Azure Storage con política de inmutabilidad;
    aquí es OneLake Files (sin inmutabilidad). Devuelve el manifiesto."""
    import os

    manifest = []
    for (operator, source), rows in sorted(files.items()):
        folder = os.path.join(root, cycle_id, operator)
        os.makedirs(folder, exist_ok=True)
        data = _csv_bytes(rows)
        name = f"payment_list_{operator}_{source}.csv"
        with open(os.path.join(folder, name), "wb") as f:
            f.write(data)
        manifest.append({"file": f"{operator}/{name}", "rows": len(rows),
                           "sha256": sha256_bytes(data)})
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
                    "holders": len(holders), "settled_payments": len(payments)},
        "exclusions_by_reason": dict(exclusions),
        "totals_by_operator": {k[1]: v for k, v in totals.items() if k[0] == "operator"},
        "totals_by_source": {k[1]: v for k, v in totals.items() if k[0] == "source"},
        "lists_sum_equals_settlement": abs(total_payments - total_lists) < 1e-6,
        "approvals": approvals,
    }
