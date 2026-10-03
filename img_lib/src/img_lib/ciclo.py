"""Apertura/cierre de la ejecución de un cuaderno: fija el id_ejecucion en los commits Delta y
escribe la fila de bitácora (Instrumento A). Cada cuaderno define su VERSION_CUADERNO."""
import uuid

from . import bitacora


def iniciar(spark, id_ciclo, id_ejecucion=None):
    id_ejecucion = id_ejecucion or f"{id_ciclo}-{uuid.uuid4().hex[:8]}"
    bitacora.marcar_commits(spark, id_ejecucion)
    return id_ejecucion, bitacora.ahora()


def cerrar(spark, *, cuaderno, version_cuaderno, etapa, id_ciclo, id_ejecucion, t0,
           pipeline_run_id=None, **kw):
    bitacora.registrar(spark, bitacora.evento(
        id_ciclo=id_ciclo, id_ejecucion=id_ejecucion, cuaderno=cuaderno,
        version_cuaderno=version_cuaderno, etapa_proceso=etapa, evento_trazabilidad="fin",
        hora_inicio=t0, hora_fin=bitacora.ahora(), pipeline_run_id=pipeline_run_id, **kw))
