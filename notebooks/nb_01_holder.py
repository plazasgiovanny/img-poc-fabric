# nb_01_holder — Tabla 8: un titular por hogar según param.holder_rule (adulta, elegible = focalizada y no bloqueada, mujer, bancarizada; desempate por edad y documento).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es cycle_id (§18.3).
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.cycle import close, start, read_cycle, read_active, write, cycle_base, rows  # noqa: F401
from img_lib import settlement
EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
CUTOFF_DATE = str(CYCLE["cutoff_date"])
base = cycle_base(spark, cycle_id)
tgt = rows(spark, "lh_gold.settlement.targeting", cycle_id)
rule = read_active(spark, "param.holder_rule", CUTOFF_DATE)
n = write(spark, settlement.select_holder(tgt, base, rule), "lh_gold.settlement.holders")

close(spark, notebook="nb_01_holder", notebook_version=NOTEBOOK_VERSION, stage="settlement",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.settlement.holders")
