# nb_04_funding_source — Tabla 8: fuente asignada a cada pago y saldo por fuente (requiere el monto). ILUSTRATIVO.

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
amt = rows(spark, "lh_gold.settlement.amount", cycle_id)
sources = read_active(spark, "param.funding_sources", CUTOFF_DATE)
payments, status = settlement.assign_funding_source(amt, sources)
n = write(spark, payments, "lh_gold.settlement.funding_source")
print(f"balance per source: {status['balance']}; payments over ceiling: {status['payments_over_ceiling']}")

close(spark, notebook="nb_04_funding_source", notebook_version=NOTEBOOK_VERSION, stage="settlement",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.settlement.funding_source")
