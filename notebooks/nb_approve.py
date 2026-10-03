# nb_approve — PLAN B (tenant sin buzón de M365): el aprobador decide ejecutando este cuaderno; el pipeline espera con Until + Wait + Lookup sobre ctl.approvals. Parámetros: control, decision (APPROVED o REJECTED), comment.

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es cycle_id (§18.3).
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)
control = "C1"
decision = "APPROVED"  # APPROVED o REJECTED
comment = None

# %% Ejecución
from img_lib.cycle import close, start, read_cycle, read_active, write, cycle_base, rows  # noqa: F401
from img_lib.run_log import now
EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
CUTOFF_DATE = str(CYCLE["cutoff_date"])
from img_lib import controls
write(spark, [controls.approval_row(cycle_id=cycle_id, control=control, decision=decision,
                                           approver=notebookutils.runtime.context.get("userName"),  # noqa: F821
                                           mechanism="approvals_table", requested_at=now(), decided_at=now(),
                                           comment=comment, pipeline_run_id=pipeline_run_id)], "ctl.approvals")
n = 1

close(spark, notebook="nb_approve", notebook_version=NOTEBOOK_VERSION, stage="control",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="ctl.approvals")
