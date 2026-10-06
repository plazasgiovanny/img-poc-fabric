"""Apertura/cierre de la ejecución de un cuaderno: fija el execution_id en los commits Delta y
escribe la fila de bitácora (Instrumento A). Cada cuaderno define su NOTEBOOK_VERSION."""
import uuid

from . import run_log


def start(spark, cycle_id, execution_id=None):
    execution_id = execution_id or f"{cycle_id}-{uuid.uuid4().hex[:8]}"
    run_log.mark_commits(spark, execution_id)
    return execution_id, run_log.now()


def read_cycle(spark, cycle_id) -> dict:  # pragma: no cover - requiere Spark/Fabric
    """El único parámetro de cada cuaderno es cycle_id (§18.3); el corte y la fecha salen de ctl.cycle."""
    rows = spark.table("ctl.cycle").where(f"cycle_id = '{cycle_id}'").collect()
    if not rows:
        raise ValueError(f"cycle {cycle_id} does not exist in ctl.cycle (run nb_init_cycle)")
    return rows[0].asDict()


def read_active(spark, table, cutoff_date) -> list:  # pragma: no cover - requiere Spark/Fabric
    """Parámetros vigentes en la fecha de corte desde param.* (los criterios son datos, no código)."""
    from .params import active
    return active([r.asDict() for r in spark.table(table).collect()], cutoff_date)


def ddl_types(rows) -> str:
    """Esquema DDL inferido de la primera muestra no nula de cada columna (string si todo es None).
    Spark no puede inferir el tipo de una columna con solo None (p. ej. household_role en la base de cruces)."""
    from datetime import date

    cols = list(dict.fromkeys(k for f in rows for k in f))
    parts = []
    for c in cols:
        vals = [f[c] for f in rows if f.get(c) is not None]
        if not vals:
            t = "string"
        elif all(isinstance(v, bool) for v in vals):
            t = "boolean"
        elif all(isinstance(v, int) and not isinstance(v, bool) for v in vals):
            t = "bigint"
        elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            t = "double"
        elif all(isinstance(v, date) for v in vals):
            t = "date"
        else:
            t = "string"
        parts.append(f"`{c}` {t}")
    return ", ".join(parts)


def extra_columns(rows, table_columns) -> list:
    """Claves de las filas que no están en las columnas de la tabla (orden de aparición)."""
    known = set(table_columns)
    return list(dict.fromkeys(k for f in rows for k in f if k not in known))


def write(spark, rows, table, mode="append") -> int:
    """Escritura estandarizada en Delta con esquema explícito. Devuelve la cantidad de filas.

    Si la tabla ya existe (por ejemplo, creada por el DDL), manda su esquema: así una columna con solo
    None conserva el tipo declarado (BIGINT, DOUBLE...) en vez de caer a string y chocar al anexar.
    Si no existe, se infiere con `ddl_types`. Si las filas traen columnas que la tabla no tiene (tabla vieja
    de una corrida anterior), falla con ValueError en vez de descartarlas en silencio."""
    if rows:
        if spark.catalog.tableExists(table):
            schema = spark.table(table).schema
            extra = extra_columns(rows, schema.names)
            if extra:
                raise ValueError(f"columns not in table {table}: {', '.join(extra)} "
                                 "(old table from a previous run: drop it or use a new cycle/table)")
        else:
            schema = ddl_types(rows)
        spark.createDataFrame(rows, schema=schema).write.format("delta").mode(mode).saveAsTable(table)
    return len(rows)


def cycle_base(spark, cycle_id) -> list:  # pragma: no cover - requiere Spark/Fabric
    """Única entrada de la Etapa 3: la base de cruces del ciclo (lh_gold)."""
    return [r.asDict() for r in spark.table("lh_gold.crosschecks.crosscheck_base").where(f"cycle_id = '{cycle_id}'").collect()]


def rows(spark, table, cycle_id) -> list:  # pragma: no cover - requiere Spark/Fabric
    return [r.asDict() for r in spark.table(table).where(f"cycle_id = '{cycle_id}'").collect()]


def close(spark, *, notebook, notebook_version, stage, cycle_id, execution_id, t0,
           pipeline_run_id=None, **kw):
    run_log.record(spark, run_log.event(
        cycle_id=cycle_id, execution_id=execution_id, notebook=notebook,
        notebook_version=notebook_version, process_stage=stage, trace_event="end",
        start_time=t0, end_time=run_log.now(), pipeline_run_id=pipeline_run_id, **kw))
