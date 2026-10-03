# nb_ctl_summary — §19: arma el resumen que ve el aprobador y deja la solicitud (decisión PENDING) en ctl.approvals. Parámetro adicional: control (C1..C4).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es cycle_id (§18.3).
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)
control = "C1"  # C1, C2, C3 o C4 (lo fija el pipeline)

# %% Ejecución
from img_lib.cycle import close, start, read_cycle, read_active, write, cycle_base, rows  # noqa: F401
from img_lib import settlement
from img_lib.run_log import now
from img_lib.crosschecks import match_pct
EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
CUTOFF_DATE = str(CYCLE["cutoff_date"])
import json
from img_lib import controls
if control == "C1":
    deliveries = [r.asDict() for r in spark.table("lh_bronze.bronze.deliveries").where(f"execution_id LIKE '{cycle_id}%'").collect()]
    quarantine = [r.asDict() for r in spark.table("lh_silver.quality.quarantine").where(f"execution_id LIKE '{cycle_id}%'").collect()]
    in_gold = {f: spark.table(f"lh_gold.sources.{f}_cutoff").where(f"cycle_id = '{cycle_id}'").count() for f in ("population", "validation")}
    res = controls.summary_c1(deliveries, quarantine, in_gold)
elif control == "C2":
    base = cycle_base(spark, cycle_id)
    res = controls.summary_c2(base, match_pct(base))
elif control == "C3":
    tgt = rows(spark, "lh_gold.settlement.targeting", cycle_id)
    payments = rows(spark, "lh_gold.settlement.funding_source", cycle_id)
    sources = read_active(spark, "param.funding_sources", CUTOFF_DATE)
    _, status = settlement.assign_funding_source([{k: p[k] for k in ("cycle_id", "household_id", "person_id", "amount", "components")} for p in payments], sources)
    res = controls.summary_c3(tgt, payments, status, sources)
else:
    res = controls.summary_c4(json.loads(notebookutils.fs.head(f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_gold.Lakehouse/Files/reports/{cycle_id}/report.json", 10**7)))  # noqa: F821
write(spark, [controls.approval_row(cycle_id=cycle_id, control=control, decision="PENDING", approver=None, mechanism="request",
                                           requested_at=now(), decided_at=None, comment="Approval request", pipeline_run_id=pipeline_run_id)], "ctl.approvals")

close(spark, notebook="nb_ctl_summary", notebook_version=NOTEBOOK_VERSION, stage="control",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=None, target_table="ctl.approvals")

# exit() termina el cuaderno: va DESPUÉS de registrar la bitácora. El pipeline muestra este resumen al aprobador.
notebookutils.notebook.exit(json.dumps(res, ensure_ascii=False, default=str))  # noqa: F821
