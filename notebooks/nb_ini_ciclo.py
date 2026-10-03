# nb_ini_ciclo — abre el ciclo: registra ctl.ciclo (corte, fecha de corte y versión de cada fuente).
# Es el ÚNICO cuaderno con parámetros de corte; los demás reciben solo id_ciclo (§18.3).
# Repetir una corrida con el mismo id_ciclo duplica filas (modo append): usar un id_ciclo nuevo por corrida.

# %% Parámetros
id_ciclo = "2026-09"
corte = "corte1"              # carpeta del landing: corte1 o corte2
fecha_corte = "2026-09-30"    # fecha de corte de las fuentes sintéticas
version_fuente_poblacional = "corte1"
version_fuente_validacion = "corte1"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"

# %% Ejecución
from datetime import date

from img_lib.bitacora import ahora
from img_lib.ciclo import cerrar, escribir, iniciar

ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
existe = spark.table("ctl.ciclo").where(f"id_ciclo = '{id_ciclo}'").count()  # noqa: F821
if existe:
    raise ValueError(f"el ciclo {id_ciclo} ya existe; usar un id_ciclo nuevo")
escribir(spark, [{"id_ciclo": id_ciclo, "corte": corte, "fecha_corte": date.fromisoformat(fecha_corte),  # noqa: F821
                  "version_fuente_poblacional": version_fuente_poblacional,
                  "version_fuente_validacion": version_fuente_validacion, "creado_en": ahora()}], "ctl.ciclo")
cerrar(spark, cuaderno="nb_ini_ciclo", version_cuaderno=VERSION_CUADERNO, etapa="inicio",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=1, tabla_destino="ctl.ciclo")
