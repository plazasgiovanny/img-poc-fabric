"""Espejo en Python de ddl/02_param_ilustrativos.sql, para pruebas locales sin Fabric.
TODO es ILUSTRATIVO: ninguno de estos valores proviene del manual de la SDIS (PENDIENTES G3 a G7).
En Fabric los cuadernos leen las tablas param.*, no este módulo."""

_VIG = {"vigente_desde": "2026-01-01", "vigente_hasta": None, "responsable": "PENDIENTE", "es_ilustrativo": 1}

CRITERIOS_FOCALIZACION = [
    {"criterio": "FOC_PLACEHOLDER_01", "campo": "grupo_sisben", "operador": "IN", "valor": "A,B", **_VIG},
]
REGLAS_BLOQUEO = [
    {"id_regla": "BLQ_PLACEHOLDER_01", "campo": "estado_validacion", "operador": "=", "valor": "FALLECIDO",
     "causal": "FALLECIDO_EN_VALIDACION", **_VIG},
    {"id_regla": "BLQ_PLACEHOLDER_02", "campo": "encontrado_validacion", "operador": "=", "valor": "NO",
     "causal": "NO_ENCONTRADO_EN_VALIDACION", **_VIG},
]
REGLA_TITULAR = [
    {"orden": 1, "criterio": "fecha_nacimiento", "direccion": "ASC", **_VIG},
    {"orden": 2, "criterio": "num_doc", "direccion": "ASC", **_VIG},
]
OPERADORES = [
    {"operador": "OPERADOR_A", "prioridad": 1, **_VIG},
    {"operador": "OPERADOR_B", "prioridad": 2, **_VIG},
]
MONTOS = [{"concepto": "MONTO_BASE_HOGAR", "monto": 100000.0, **_VIG}]
FUENTES_RECURSOS = [{"fuente_recursos": "FUENTE_X", "techo": 50_000_000.0, **_VIG}]
