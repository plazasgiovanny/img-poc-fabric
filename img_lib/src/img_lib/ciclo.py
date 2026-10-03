"""Apertura/cierre de la ejecución de un cuaderno: fija el id_ejecucion en los commits Delta y
escribe la fila de bitácora (Instrumento A). Cada cuaderno define su VERSION_CUADERNO."""
import uuid

from . import bitacora


def iniciar(spark, id_ciclo, id_ejecucion=None):
    id_ejecucion = id_ejecucion or f"{id_ciclo}-{uuid.uuid4().hex[:8]}"
    bitacora.marcar_commits(spark, id_ejecucion)
    return id_ejecucion, bitacora.ahora()


def leer_ciclo(spark, id_ciclo) -> dict:  # pragma: no cover - requiere Spark/Fabric
    """El único parámetro de cada cuaderno es id_ciclo (§18.3); el corte y la fecha salen de ctl.ciclo."""
    filas = spark.table("ctl.ciclo").where(f"id_ciclo = '{id_ciclo}'").collect()
    if not filas:
        raise ValueError(f"ciclo {id_ciclo} no existe en ctl.ciclo (ejecutar nb_ini_ciclo)")
    return filas[0].asDict()


def leer_vigentes(spark, tabla, fecha_corte) -> list:  # pragma: no cover - requiere Spark/Fabric
    """Parámetros vigentes en la fecha de corte desde param.* (los criterios son datos, no código)."""
    from .params import vigentes
    return vigentes([r.asDict() for r in spark.table(tabla).collect()], fecha_corte)


def ddl_tipos(filas) -> str:
    """Esquema DDL inferido de la primera muestra no nula de cada columna (string si todo es None).
    Spark no puede inferir el tipo de una columna con solo None (p. ej. rol_hogar en la base de cruces)."""
    from datetime import date

    cols = list(dict.fromkeys(k for f in filas for k in f))
    partes = []
    for c in cols:
        vals = [f[c] for f in filas if f.get(c) is not None]
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
        partes.append(f"`{c}` {t}")
    return ", ".join(partes)


def escribir(spark, filas, tabla, modo="append") -> int:  # pragma: no cover - requiere Spark/Fabric
    """Escritura estandarizada en Delta con esquema explícito. Devuelve la cantidad de filas."""
    if filas:
        spark.createDataFrame(filas, schema=ddl_tipos(filas)).write.format("delta").mode(modo).saveAsTable(tabla)
    return len(filas)


def base_del_ciclo(spark, id_ciclo) -> list:  # pragma: no cover - requiere Spark/Fabric
    """Única entrada de la Etapa 3: la base de cruces del ciclo (lh_oro)."""
    return [r.asDict() for r in spark.table("lh_oro.cruces.base_cruces").where(f"id_ciclo = '{id_ciclo}'").collect()]


def filas(spark, tabla, id_ciclo) -> list:  # pragma: no cover - requiere Spark/Fabric
    return [r.asDict() for r in spark.table(tabla).where(f"id_ciclo = '{id_ciclo}'").collect()]


def cerrar(spark, *, cuaderno, version_cuaderno, etapa, id_ciclo, id_ejecucion, t0,
           pipeline_run_id=None, **kw):
    bitacora.registrar(spark, bitacora.evento(
        id_ciclo=id_ciclo, id_ejecucion=id_ejecucion, cuaderno=cuaderno,
        version_cuaderno=version_cuaderno, etapa_proceso=etapa, evento_trazabilidad="fin",
        hora_inicio=t0, hora_fin=bitacora.ahora(), pipeline_run_id=pipeline_run_id, **kw))
