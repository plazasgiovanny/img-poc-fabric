# nb_03_amount — Tabla 8: monto liquidado por hogar y sus componentes. monto base de param.amounts (120000 por el diccionario de dispersión).

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
hld = rows(spark, "lh_gold.settlement.holders", cycle_id)
amounts = read_active(spark, "param.amounts", CUTOFF_DATE)
n = write(spark, settlement.calculate_amount(hld, amounts), "lh_gold.settlement.amount")

close(spark, notebook="nb_03_amount", notebook_version=NOTEBOOK_VERSION, stage="settlement",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.settlement.amount")
