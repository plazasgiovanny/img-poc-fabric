# nb_e1_gold — Etapa 1 (§16): una tabla por fuente y por corte con person_id/household_id ya asignados.
# Oro es la ÚNICA entrada permitida para los cruces: ningún cuaderno posterior lee Bronce ni Plata.

# %% Parámetros
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"

# %% Ejecución
from img_lib.cycle import close, start, read_cycle

EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
cutoff = read_cycle(spark, cycle_id)["cutoff"]  # noqa: F821
where_clause = f"cycle_id = '{cycle_id}' AND cutoff = '{cutoff}'"
xref = spark.table("lh_silver.mdm.xref").where(where_clause)  # noqa: F821
person = spark.table("lh_silver.mdm.person").where(where_clause).select("person_id", "household_id")  # noqa: F821
n = 0
for source in ("population", "validation"):
    rec = spark.table(f"lh_silver.{source}.records").where(where_clause)  # noqa: F821
    x = xref.where(f"source = '{source}'").select("origin_id", "person_id")
    gold = rec.join(x, "origin_id", "inner").join(person, "person_id", "inner")
    n += gold.count()
    gold.write.format("delta").mode("append").saveAsTable(f"lh_gold.sources.{source}_cutoff")  # noqa: F821

close(spark, notebook="nb_e1_gold", notebook_version=NOTEBOOK_VERSION, stage="gold",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.sources.*_cutoff")
