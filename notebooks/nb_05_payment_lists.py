# nb_05_payment_lists — Tabla 8: sábana del ciclo (los .xlsx por operador se generan al publicar).

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
payments = rows(spark, "lh_gold.settlement.funding_source", cycle_id)
mp = rows(spark, "lh_gold.settlement.payment_method", cycle_id)
master_sheet, _ = settlement.generate_payment_lists(payments, mp, base)
n = write(spark, master_sheet, "lh_gold.settlement.payment_list")

close(spark, notebook="nb_05_payment_lists", notebook_version=NOTEBOOK_VERSION, stage="payment_lists",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.settlement.payment_list")
