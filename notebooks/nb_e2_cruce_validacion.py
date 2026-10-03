# nb_e2_cruce_validacion — Etapa 2 (§17): familia de fuentes «validacion». Lee SOLO de Oro (única entrada permitida para los cruces).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib.cruces import primera_por_persona
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
filtro_corte = CICLO["corte"]
oro = [r.asDict() for r in spark.table("lh_oro.fuentes.validacion_corte").where(f"id_ciclo = '{id_ciclo}' AND corte = '{filtro_corte}'").collect()]
stg = list(primera_por_persona(oro).values())
n = escribir(spark, stg, "lh_oro.cruces.stg_validacion", "append")

cerrar(spark, cuaderno="nb_e2_cruce_validacion", version_cuaderno=VERSION_CUADERNO, etapa="cruces",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.cruces.stg_validacion")
