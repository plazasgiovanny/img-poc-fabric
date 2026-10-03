# nb_registrar_aprobacion — §19: registra la decisión (APROBADO, RECHAZADO o VENCIDO) con aprobador y hora. Parámetros adicionales: control, decision, aprobador, mecanismo, comentario.

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)
control = "C1"
decision = "APROBADO"  # APROBADO, RECHAZADO o VENCIDO
aprobador = None  # si es None, se toma el usuario de la sesión
mecanismo = "approval_activity"
comentario = None

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib.bitacora import ahora
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
from img_lib import controles
if aprobador is None:
    aprobador = notebookutils.runtime.context.get("userName")  # noqa: F821  VERIFICAR (G10): la Approval activity puede traer al aprobador
escribir(spark, [controles.fila_aprobacion(id_ciclo=id_ciclo, control=control, decision=decision, aprobador=aprobador,
                                           mecanismo=mecanismo, solicitado_en=ahora(), decidido_en=ahora(),
                                           comentario=comentario, pipeline_run_id=pipeline_run_id)], "ctl.aprobaciones")
n = 1

cerrar(spark, cuaderno="nb_registrar_aprobacion", version_cuaderno=VERSION_CUADERNO, etapa="control",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="ctl.aprobaciones")
