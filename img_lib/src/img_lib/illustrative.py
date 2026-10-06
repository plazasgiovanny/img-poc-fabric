"""Espejo en Python de ddl/02_param_illustrative.sql, para pruebas locales sin Fabric.
Las reglas de focalización, bloqueo y titular provienen de lo definido por el equipo de la fuente (SDIS);
`is_illustrative = 1` queda solo en lo inventado para la demo (fuentes de financiación, partición de
listados, prioridad de operadores). En Fabric los cuadernos leen las tablas param.*, no este módulo."""
from . import mapping

_VALIDITY = {"valid_from": "2026-01-01", "valid_to": None, "owner": "SDIS", "is_illustrative": 0}
_DEMO = {"valid_from": "2026-01-01", "valid_to": None, "owner": "PENDING", "is_illustrative": 1}

TARGETING_CRITERIA = [
    {"criterion": "SISBEN_GROUP_A", "field": "sisben_group", "operator": "=", "value": mapping.GROUP_TARGET,
     "support_document": "RSH_grupo_S4 = '1. SISBEN IV - A'", **_VALIDITY},
]
BLOCK_RULES = [
    {"rule_id": "BLOCK_RENEC", "field": "renec_validity", "operator": "NOT IN", "value": "0,12",
     "reason": "RENEC_NOT_VALID", "support_document": "RSH_vigencia_renec NOT IN (0,12)", **_VALIDITY},
    {"rule_id": "BLOCK_DECEASED_REGISTRY", "field": "validation_found", "operator": "=", "value": "YES",
     "reason": "IN_DECEASED_REGISTRY", "support_document": "existe en la base de inhumados (tipo + número)",
     **_VALIDITY},
]
# sort_direction: ASC / DESC ordenan; REQUIRED exige que el criterio sea verdadero (filtro del titular).
HOLDER_RULE = [
    {"rank": 1, "criterion": "is_adult", "sort_direction": "REQUIRED", **_VALIDITY},
    {"rank": 2, "criterion": "is_not_blocked", "sort_direction": "REQUIRED", **_VALIDITY},
    {"rank": 3, "criterion": "is_woman", "sort_direction": "DESC", **_VALIDITY},
    {"rank": 4, "criterion": "is_banked", "sort_direction": "DESC", **_VALIDITY},
    {"rank": 5, "criterion": "age", "sort_direction": "DESC", **_VALIDITY},
    {"rank": 6, "criterion": "doc_number", "sort_direction": "ASC", **_VALIDITY},
]
# El primer operador por prioridad es el de respaldo cuando la titular no tiene operador (SIN OPERADOR).
OPERATORS = [
    {"operator": "EFECTY", "priority": 1, **_DEMO},
    {"operator": "DAVIPLATA", "priority": 2, **_DEMO},
    {"operator": "NEQUI", "priority": 3, **_DEMO},
    {"operator": "ALM", "priority": 4, **_DEMO},
    {"operator": "MOVII", "priority": 5, **_DEMO},
    {"operator": "DALE", "priority": 6, **_DEMO},
    {"operator": "POWWI", "priority": 7, **_DEMO},
]
AMOUNTS = [{"concept": "BASE_HOUSEHOLD_AMOUNT", "amount": 120000.0, "owner": "SDIS", "valid_from": "2026-01-01",
            "valid_to": None, "is_illustrative": 0}]
FUNDING_SOURCES = [{"funding_source": "SOURCE_X", "ceiling": 100_000_000.0, **_DEMO}]
PAYMENT_LIST_PARTITION = [{"split_by": "operator", **_DEMO}]
