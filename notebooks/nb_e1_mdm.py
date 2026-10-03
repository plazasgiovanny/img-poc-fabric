# nb_e1_mdm — Etapa 1 (§16): maestro de personas y de hogares sobre Plata, con reglas de
# coincidencia y supervivencia. Reglas por defecto ILUSTRATIVAS (PENDIENTE G6), ver img_lib.mdm.
# PoC (500-5.000 registros): se procesa en el driver; para volúmenes reales se migraría a Spark.

# %% Parámetros
id_ciclo = "2026-09"
corte = 1
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"

# %% Ejecución
import json

from img_lib import mdm
from img_lib.ciclo import cerrar, iniciar

ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
regs = []
for fuente in ("poblacional", "validacion"):
    for r in (spark.table(f"lh_plata.{fuente}.registros")  # noqa: F821
              .where(f"id_ciclo = '{id_ciclo}' AND fecha_corte = 'corte{corte}'").collect()):
        d = r.asDict()
        d["fuente"] = fuente
        d["id_hogar_origen"] = d.get("id_hogar_origen")
        regs.append(d)

personas, xref = mdm.construir_maestro(regs)
hogares, asign = mdm.construir_hogares(personas)
for p in personas:
    p["id_hogar"] = asign[p["id_persona"]]
    p["fuente_ganadora_por_atributo"] = json.dumps(p["fuente_ganadora_por_atributo"])
    p["id_ciclo"], p["fecha_corte"] = id_ciclo, f"corte{corte}"
for h in hogares:
    h["id_ciclo"], h["fecha_corte"] = id_ciclo, f"corte{corte}"
for x in xref:
    x["id_ciclo"], x["fecha_corte"] = id_ciclo, f"corte{corte}"

for tabla, datos in (("mdm.persona", personas), ("mdm.hogar", hogares), ("mdm.xref", xref)):
    spark.createDataFrame(datos).write.format("delta").mode("append") \
        .saveAsTable(f"lh_plata.{tabla}")  # noqa: F821

cerrar(spark, cuaderno="nb_e1_mdm", version_cuaderno=VERSION_CUADERNO, etapa="mdm",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=len(regs), tabla_destino="lh_plata.mdm.*")
