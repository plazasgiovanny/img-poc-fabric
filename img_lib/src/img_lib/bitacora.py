"""Bitácora de ejecución (§18, Instrumento A / Tabla 2 + trazabilidad Tabla 7).

`evento()` construye la fila (puro Python, testeable). `registrar()` la escribe en
ctl.bitacora_ejecucion y marca los commits Delta con `userMetadata = id_ejecucion`, de modo
que `DESCRIBE HISTORY` pueda cruzarse con la bitácora (criterio de auditoría 100 %, §7 Exp. 2)."""
from datetime import datetime, timezone

from . import __version__

CAMPOS_INSTRUMENTO_A = (
    "id_lote", "fecha_ciclo", "hora_inicio", "hora_fin", "num_registros_procesados",
    "horas_hombre_manual", "num_errores_duplicidad", "etapa_proceso", "modo_procesamiento",
    "evento_trazabilidad", "fuente_dato", "observaciones",
)
CAMPOS_TRAZABILIDAD = (
    "id_ciclo", "id_ejecucion", "pipeline_run_id", "cuaderno", "version_cuaderno",
    "version_lib", "usuario", "tabla_destino", "version_delta_destino", "hash_salida",
)
TABLA_BITACORA = "ctl.bitacora_ejecucion"


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def evento(*, id_ciclo, id_ejecucion, cuaderno, version_cuaderno, etapa_proceso,
           evento_trazabilidad, hora_inicio=None, hora_fin=None, fuente_dato=None,
           num_registros_procesados=None, num_errores_duplicidad=None,
           horas_hombre_manual=None, modo_procesamiento="automatico",
           tabla_destino=None, version_delta_destino=None, hash_salida=None,
           pipeline_run_id=None, usuario=None, observaciones=None) -> dict:
    """id_lote == id_ejecucion. `horas_hombre_manual` es tiempo humano (esperas/decisiones de
    control), separado del tiempo de cómputo (hora_fin - hora_inicio)."""
    return {
        "id_lote": id_ejecucion, "fecha_ciclo": id_ciclo, "hora_inicio": hora_inicio or ahora(),
        "hora_fin": hora_fin, "num_registros_procesados": num_registros_procesados,
        "horas_hombre_manual": horas_hombre_manual,
        "num_errores_duplicidad": num_errores_duplicidad, "etapa_proceso": etapa_proceso,
        "modo_procesamiento": modo_procesamiento, "evento_trazabilidad": evento_trazabilidad,
        "fuente_dato": fuente_dato, "observaciones": observaciones,
        "id_ciclo": id_ciclo, "id_ejecucion": id_ejecucion, "pipeline_run_id": pipeline_run_id,
        "cuaderno": cuaderno, "version_cuaderno": version_cuaderno, "version_lib": __version__,
        "usuario": usuario, "tabla_destino": tabla_destino,
        "version_delta_destino": version_delta_destino, "hash_salida": hash_salida,
    }


def marcar_commits(spark, id_ejecucion: str) -> None:
    """Todo commit Delta posterior queda etiquetado con el id_ejecucion."""
    spark.conf.set("spark.databricks.delta.commitInfo.userMetadata", id_ejecucion)


def registrar(spark, fila: dict) -> None:  # pragma: no cover - requiere Spark/Fabric
    spark.createDataFrame([fila]).write.format("delta").mode("append").saveAsTable(TABLA_BITACORA)
