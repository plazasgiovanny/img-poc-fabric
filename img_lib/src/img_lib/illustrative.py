"""Espejo en Python de ddl/02_param_illustrative.sql, para pruebas locales sin Fabric.
TODO es ILUSTRATIVO: ninguno de estos valores proviene del manual de la SDIS (PENDIENTES G3 a G7).
En Fabric los cuadernos leen las tablas param.*, no este módulo."""

_VALIDITY = {"valid_from": "2026-01-01", "valid_to": None, "owner": "PENDING", "is_illustrative": 1}

TARGETING_CRITERIA = [
    {"criterion": "TARGETING_PLACEHOLDER_01", "field": "sisben_group", "operator": "IN", "value": "A,B", **_VALIDITY},
]
BLOCK_RULES = [
    {"rule_id": "BLOCK_PLACEHOLDER_01", "field": "validation_status", "operator": "=", "value": "DECEASED",
     "reason": "DECEASED_IN_VALIDATION", **_VALIDITY},
    {"rule_id": "BLOCK_PLACEHOLDER_02", "field": "validation_found", "operator": "=", "value": "NO",
     "reason": "NOT_FOUND_IN_VALIDATION", **_VALIDITY},
]
HOLDER_RULE = [
    {"rank": 1, "criterion": "birth_date", "sort_direction": "ASC", **_VALIDITY},
    {"rank": 2, "criterion": "doc_number", "sort_direction": "ASC", **_VALIDITY},
]
OPERATORS = [
    {"operator": "OPERATOR_A", "priority": 1, **_VALIDITY},
    {"operator": "OPERATOR_B", "priority": 2, **_VALIDITY},
]
AMOUNTS = [{"concept": "BASE_HOUSEHOLD_AMOUNT", "amount": 100000.0, **_VALIDITY}]
FUNDING_SOURCES = [{"funding_source": "SOURCE_X", "ceiling": 50_000_000.0, **_VALIDITY}]
