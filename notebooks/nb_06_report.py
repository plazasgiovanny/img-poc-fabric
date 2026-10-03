# nb_06_report — Tabla 8: informe de generación (lee la bitácora y las aprobaciones). Idempotente: se ejecuta antes de C4 y al cierre, ya con C4.

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
import json
base = cycle_base(spark, cycle_id)
tgt = rows(spark, "lh_gold.settlement.targeting", cycle_id)
hld = rows(spark, "lh_gold.settlement.holders", cycle_id)
payments = rows(spark, "lh_gold.settlement.funding_source", cycle_id)
master_sheet = rows(spark, "lh_gold.settlement.payment_list", cycle_id)
appr = [{k: str(v) for k, v in r.items()} for r in rows(spark, "ctl.approvals", cycle_id)]
versions = {r["notebook"]: r["notebook_version"] for r in rows(spark, "ctl.run_log", cycle_id)}
param = {t: read_active(spark, f"param.{t}", CUTOFF_DATE) for t in
         ("targeting_criteria", "block_rules", "holder_rule", "operators", "amounts", "funding_sources")}
report = settlement.build_report(
    cycle_id=cycle_id, cutoff_date=CUTOFF_DATE,
    source_versions={"population": CYCLE["population_source_version"], "validation": CYCLE["validation_source_version"]},
    applied_params=param, notebook_versions=versions, base=base, targeting=tgt, holders=hld,
    payments=payments, master_sheet=master_sheet, approvals=appr)
path = f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_gold.Lakehouse/Files/reports/{cycle_id}/report.json"
notebookutils.fs.put(path, json.dumps(report, ensure_ascii=False, indent=2, default=str), True)  # noqa: F821
n = len(master_sheet)

close(spark, notebook="nb_06_report", notebook_version=NOTEBOOK_VERSION, stage="report",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.Files/reports")
