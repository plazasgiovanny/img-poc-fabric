# nb_e1_oro — Etapa 1 (§16): una tabla por fuente y por corte con id_persona/id_hogar ya asignados.
# Oro es la ÚNICA entrada permitida para los cruces: ningún cuaderno posterior lee Bronce ni Plata.

# %% Parámetros
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo

ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
corte = leer_ciclo(spark, id_ciclo)["corte"]  # noqa: F821
filtro = f"id_ciclo = '{id_ciclo}' AND corte = '{corte}'"
xref = spark.table("lh_plata.mdm.xref").where(filtro)  # noqa: F821
persona = spark.table("lh_plata.mdm.persona").where(filtro).select("id_persona", "id_hogar")  # noqa: F821
n = 0
for fuente in ("poblacional", "validacion"):
    reg = spark.table(f"lh_plata.{fuente}.registros").where(filtro)  # noqa: F821
    x = xref.where(f"fuente = '{fuente}'").select("id_origen", "id_persona")
    oro = reg.join(x, "id_origen", "inner").join(persona, "id_persona", "inner")
    n += oro.count()
    oro.write.format("delta").mode("append").saveAsTable(f"lh_oro.fuentes.{fuente}_corte")  # noqa: F821

cerrar(spark, cuaderno="nb_e1_oro", version_cuaderno=VERSION_CUADERNO, etapa="oro",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.fuentes.*_corte")
