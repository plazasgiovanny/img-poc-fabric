# nb_e2_crosscheck_population — Etapa 2 (§17): familia de fuentes «poblacional». Lee SOLO de Oro (única entrada permitida para los cruces).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es cycle_id (§18.3).
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.cycle import close, start, read_cycle, read_active, write, cycle_base, rows  # noqa: F401
from img_lib.crosschecks import first_per_person
EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
CUTOFF_DATE = str(CYCLE["cutoff_date"])
cutoff_filter = CYCLE["cutoff"]
gold = [r.asDict() for r in spark.table("lh_gold.sources.population_cutoff").where(f"cycle_id = '{cycle_id}' AND cutoff = '{cutoff_filter}'").collect()]
stg = list(first_per_person(gold).values())
n = write(spark, stg, "lh_gold.crosschecks.stg_population", "append")

close(spark, notebook="nb_e2_crosscheck_population", notebook_version=NOTEBOOK_VERSION, stage="crosschecks",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.crosschecks.stg_population")
