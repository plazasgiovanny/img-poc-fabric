# nb_05_listados — Tabla 8: sábana del ciclo (archivos por operador y fuente se generan al publicar).

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
pagos = filas(spark, "lh_oro.liquidacion.fuente_recursos", id_ciclo)
mp = filas(spark, "lh_oro.liquidacion.medio_pago", id_ciclo)
sabana, _ = liquidacion.generar_listados(pagos, mp, base)
n = escribir(spark, sabana, "lh_oro.liquidacion.listado")

cerrar(spark, cuaderno="nb_05_listados", version_cuaderno=VERSION_CUADERNO, etapa="listados",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.liquidacion.listado")
