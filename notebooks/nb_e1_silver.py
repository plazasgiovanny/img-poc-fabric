# nb_e1_silver — Etapa 1 (§16): aplica el mapeo RSH_* -> nombres internos (img_lib.mapping) y normaliza documento, nombres, fechas, sexo, edad y localidad;
# elimina duplicados exactos DENTRO de cada fuente; aplica reglas de calidad. Lo que incumple va a
# quality.quarantine con la causa del rechazo. (PoC: una sola función para ambas fuentes.)

# %% Parámetros
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"

# %% Ejecución
from datetime import date

from img_lib import mapping
from img_lib.cycle import close, write, start, read_cycle
from img_lib.validate import validate_record

EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
cutoff = read_cycle(spark, cycle_id)["cutoff"]  # noqa: F821
today = date.today()
total, dup_errors = 0, 0

for source in ("population", "validation"):
    rows = [r.asDict() for r in spark.table(f"lh_bronze.bronze.{source}_raw")  # noqa: F821
             .where(f"_cycle_id = '{cycle_id}' AND _cutoff_date = '{cutoff}'").collect()]
    ok, rejected, seen = [], [], set()
    for r in rows:
        mapped = mapping.to_internal(r, source)  # Bronce (RSH_*) -> nombres internos
        rec, causes = validate_record(mapped, today=today)
        if causes:
            rejected.append({"source": source, "origin_id": mapped.get("origin_id"), "rule": ";".join(causes),
                               "cause": ";".join(causes), "value": str(mapped.get("doc_number")),
                               "execution_id": EXEC_ID})
            continue
        key = (rec["doc_type"], rec["doc_number"], rec.get("first_names"), rec.get("last_names"), rec.get("birth_date"))
        if key in seen:  # duplicado exacto dentro de la fuente
            dup_errors += 1
            continue
        seen.add(key)
        rec["cycle_id"], rec["cutoff"] = cycle_id, cutoff
        ok.append(rec)
    total += len(rows)
    write(spark, ok, f"lh_silver.{source}.records")  # noqa: F821
    write(spark, rejected, "lh_silver.quality.quarantine")  # noqa: F821

close(spark, notebook="nb_e1_silver", notebook_version=NOTEBOOK_VERSION, stage="silver",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=total, duplicate_errors=dup_errors,
       target_table="lh_silver.*.records")
