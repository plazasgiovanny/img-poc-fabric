# nb_record_approval — §19: registra la decisión (APROBADO, RECHAZADO o VENCIDO) con aprobador y hora. Parámetros adicionales: control, decision, aprobador, mecanismo, comentario.

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es cycle_id (§18.3).
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)
control = "C1"
decision = "APPROVED"  # APROBADO, RECHAZADO o VENCIDO
approver = None  # si es None, se toma el usuario de la sesión
mechanism = "approval_activity"
comment = None

# %% Ejecución
from img_lib.cycle import close, start, read_cycle, read_active, write, cycle_base, rows  # noqa: F401
from img_lib.run_log import now
EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
CUTOFF_DATE = str(CYCLE["cutoff_date"])
from img_lib import controls
if approver is None:
    approver = notebookutils.runtime.context.get("userName")  # noqa: F821  VERIFICAR (G10): la Approval activity puede traer al aprobador
write(spark, [controls.approval_row(cycle_id=cycle_id, control=control, decision=decision, approver=approver,
                                           mechanism=mechanism, requested_at=now(), decided_at=now(),
                                           comment=comment, pipeline_run_id=pipeline_run_id)], "ctl.approvals")
n = 1

close(spark, notebook="nb_record_approval", notebook_version=NOTEBOOK_VERSION, stage="control",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="ctl.approvals")
