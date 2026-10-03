# nb_init_cycle — abre el ciclo: registra ctl.cycle (corte, fecha de corte y versión de cada fuente).
# Es el ÚNICO cuaderno con parámetros de corte; los demás reciben solo cycle_id (§18.3).
# Repetir una corrida con el mismo cycle_id duplica filas (modo append): usar un cycle_id nuevo por corrida.

# %% Parámetros
cycle_id = "2026-09"
cutoff = "cutoff1"              # carpeta del landing: cutoff1 o cutoff2
cutoff_date = "2026-09-30"    # fecha de corte de las fuentes sintéticas
population_source_version = "cutoff1"
validation_source_version = "cutoff1"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"

# %% Ejecución
from datetime import date

from img_lib.run_log import now
from img_lib.cycle import close, write, start

EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
already_exists = spark.table("ctl.cycle").where(f"cycle_id = '{cycle_id}'").count()  # noqa: F821
if already_exists:
    raise ValueError(f"cycle {cycle_id} already exists; use a new cycle_id")
write(spark, [{"cycle_id": cycle_id, "cutoff": cutoff, "cutoff_date": date.fromisoformat(cutoff_date),  # noqa: F821
                  "population_source_version": population_source_version,
                  "validation_source_version": validation_source_version, "created_at": now()}], "ctl.cycle")
close(spark, notebook="nb_init_cycle", notebook_version=NOTEBOOK_VERSION, stage="start",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=1, target_table="ctl.cycle")
