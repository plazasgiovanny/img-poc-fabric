# nb_01_titular — Tabla 8: un titular por hogar según param.regla_titular (orden de criterios parametrizado, PENDIENTE G5).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib import liquidacion
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
base = base_del_ciclo(spark, id_ciclo)
foc = filas(spark, "lh_oro.liquidacion.focalizacion", id_ciclo)
regla = leer_vigentes(spark, "param.regla_titular", FECHA_CORTE)
n = escribir(spark, liquidacion.seleccionar_titular(foc, base, regla), "lh_oro.liquidacion.titulares")

cerrar(spark, cuaderno="nb_01_titular", version_cuaderno=VERSION_CUADERNO, etapa="liquidacion",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.liquidacion.titulares")
