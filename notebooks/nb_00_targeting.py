# nb_00_targeting — Tabla 8: elegibles y excluidos, cada exclusión con su causal. Criterios y reglas son DATOS (param.*).

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
criteria = read_active(spark, "param.targeting_criteria", CUTOFF_DATE)
blocks = read_active(spark, "param.block_rules", CUTOFF_DATE)
res = settlement.target(base, criteria, blocks)
n = write(spark, res, "lh_gold.settlement.targeting")

close(spark, notebook="nb_00_targeting", notebook_version=NOTEBOOK_VERSION, stage="settlement",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.settlement.targeting")
