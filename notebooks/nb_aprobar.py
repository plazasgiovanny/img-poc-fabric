# nb_aprobar — PLAN B (tenant sin buzón de M365): el aprobador decide ejecutando este cuaderno; el pipeline espera con Until + Wait + Lookup sobre ctl.aprobaciones. Parámetros: control, decision (APROBADO o RECHAZADO), comentario.

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)
control = "C1"
decision = "APROBADO"  # APROBADO o RECHAZADO
comentario = None

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib.bitacora import ahora
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
from img_lib import controles
escribir(spark, [controles.fila_aprobacion(id_ciclo=id_ciclo, control=control, decision=decision,
                                           aprobador=notebookutils.runtime.context.get("userName"),  # noqa: F821
                                           mecanismo="tabla_aprobaciones", solicitado_en=ahora(), decidido_en=ahora(),
                                           comentario=comentario, pipeline_run_id=pipeline_run_id)], "ctl.aprobaciones")
n = 1

cerrar(spark, cuaderno="nb_aprobar", version_cuaderno=VERSION_CUADERNO, etapa="control",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="ctl.aprobaciones")
