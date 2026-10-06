# nb_07_publish — Adaptación de la PoC al §18.4: publica en OneLake Files (carpeta por ciclo y operador con el listado .xlsx de 32 columnas y huella SHA-256). Producción: Azure Storage con política de inmutabilidad. SOLO se ejecuta si C1 a C4 están APROBADOS.

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
from img_lib import controls
appr = rows(spark, "ctl.approvals", cycle_id)
appr = [{**a, "decided_at": str(a["decided_at"] or "")} for a in appr]
if not controls.all_approved(appr, cycle_id):
    raise RuntimeError("Not publishing: some controls are not approved (expired or missing = rejected, §19)")
base = cycle_base(spark, cycle_id)
payments = rows(spark, "lh_gold.settlement.funding_source", cycle_id)
mp = rows(spark, "lh_gold.settlement.payment_method", cycle_id)
_, files = settlement.generate_payment_lists(payments, mp, base)
tmp = "/tmp/publication"
manifest = settlement.publish(files, tmp, cycle_id)
destination = f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_gold.Lakehouse/Files/publication/{cycle_id}"
notebookutils.fs.cp(f"file:{tmp}/{cycle_id}", destination, True)  # noqa: F821  copia recursiva a lh_gold
n = sum(m["rows"] for m in manifest)

close(spark, notebook="nb_07_publish", notebook_version=NOTEBOOK_VERSION, stage="publication",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=n, target_table="lh_gold.Files/publication")
