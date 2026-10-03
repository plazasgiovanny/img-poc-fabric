# nb_e2_consolidation — Etapa 2 (§17): consolida la base de cruces, una fila por persona y ciclo. Registra HECHOS, no decisiones (Tabla 7).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es cycle_id (§18.3).
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.cycle import close, start, read_cycle, read_active, write, cycle_base, rows  # noqa: F401
from img_lib.run_log import now
from img_lib.crosschecks import build_base, match_pct
EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
CUTOFF_DATE = str(CYCLE["cutoff_date"])
pop = rows(spark, "lh_gold.crosschecks.stg_population", cycle_id)
val = rows(spark, "lh_gold.crosschecks.stg_validation", cycle_id)
base = build_base(
    pop, val, cycle_id=cycle_id, cutoff_date=CUTOFF_DATE,
    source_versions={"population": CYCLE["population_source_version"], "validation": CYCLE["validation_source_version"]},
    execution_id=EXEC_ID, notebook_version=NOTEBOOK_VERSION, ts=now())
n = write(spark, base, "lh_gold.crosschecks.crosscheck_base", "append")
print(f"crosschecks: {n} people; % found in validation = {match_pct(base):.2f}")

close(spark, notebook="nb_e2_consolidation", notebook_version=NOTEBOOK_VERSION, stage="crosschecks",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.crosschecks.crosscheck_base")
