"""Bitácora de ejecución (§18, Instrumento A / Tabla 2 + trazabilidad Tabla 7).

`event()` construye la fila (puro Python, testeable). `record()` la escribe en
ctl.run_log y marca los commits Delta con `userMetadata = execution_id`, de modo
que `DESCRIBE HISTORY` pueda cruzarse con la bitácora (criterio de auditoría 100 %, §7 Exp. 2)."""
from datetime import datetime, timezone

from . import __version__

INSTRUMENT_A_FIELDS = (
    "batch_id", "cycle_date", "start_time", "end_time", "records_processed",
    "manual_labor_hours", "duplicate_errors", "process_stage", "processing_mode",
    "trace_event", "data_source", "notes",
)
TRACEABILITY_FIELDS = (
    "cycle_id", "execution_id", "pipeline_run_id", "notebook", "notebook_version",
    "version_lib", "user_name", "target_table", "delta_target_version", "output_hash",
)
RUN_LOG_TABLE = "ctl.run_log"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def event(*, cycle_id, execution_id, notebook, notebook_version, process_stage,
           trace_event, start_time=None, end_time=None, data_source=None,
           records_processed=None, duplicate_errors=None,
           manual_labor_hours=None, processing_mode="automatic",
           target_table=None, delta_target_version=None, output_hash=None,
           pipeline_run_id=None, user_name=None, notes=None) -> dict:
    """batch_id == execution_id. `manual_labor_hours` es tiempo humano (esperas/decisiones de
    control), separado del tiempo de cómputo (end_time - start_time)."""
    return {
        "batch_id": execution_id, "cycle_date": cycle_id, "start_time": start_time or now(),
        "end_time": end_time, "records_processed": records_processed,
        "manual_labor_hours": manual_labor_hours,
        "duplicate_errors": duplicate_errors, "process_stage": process_stage,
        "processing_mode": processing_mode, "trace_event": trace_event,
        "data_source": data_source, "notes": notes,
        "cycle_id": cycle_id, "execution_id": execution_id, "pipeline_run_id": pipeline_run_id,
        "notebook": notebook, "notebook_version": notebook_version, "version_lib": __version__,
        "user_name": user_name, "target_table": target_table,
        "delta_target_version": delta_target_version, "output_hash": output_hash,
    }


def mark_commits(spark, execution_id: str) -> None:
    """Todo commit Delta posterior queda etiquetado con el execution_id."""
    spark.conf.set("spark.databricks.delta.commitInfo.userMetadata", execution_id)


def record(spark, row: dict, table: str = RUN_LOG_TABLE) -> None:
    """Escribe la fila en la bitácora. Usa `cycle.write` para que las columnas con None (data_source, notes,
    output_hash...) tomen el tipo de la tabla en vez de fallar al inferir el esquema."""
    from .cycle import write  # import diferido: cycle importa este módulo
    write(spark, [row], table)
