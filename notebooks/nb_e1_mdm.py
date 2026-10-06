# nb_e1_mdm — Etapa 1 (§16): maestro de personas y de hogares sobre Plata, con reglas de
# coincidencia y supervivencia. Identidad = tipo + número de documento; ver img_lib.mdm.
# PoC (500-5.000 registros): se procesa en el driver; para volúmenes reales se migraría a Spark.

# %% Parámetros
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"

# %% Ejecución
import json

from img_lib import mdm
from img_lib.cycle import close, write, start, read_cycle

EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
cutoff = read_cycle(spark, cycle_id)["cutoff"]  # noqa: F821
recs = []
for source in ("population", "validation"):
    for r in (spark.table(f"lh_silver.{source}.records")  # noqa: F821
              .where(f"cycle_id = '{cycle_id}' AND cutoff = '{cutoff}'").collect()):
        d = r.asDict()
        d["source"] = source
        d["origin_household_id"] = d.get("origin_household_id")
        recs.append(d)

people, xref = mdm.build_master(recs)
households, assign = mdm.build_households(people)
for p in people:
    p["household_id"] = assign[p["person_id"]]
    p["winning_source_by_attribute"] = json.dumps(p["winning_source_by_attribute"])
    p["cycle_id"], p["cutoff"] = cycle_id, cutoff
for h in households:
    h["cycle_id"], h["cutoff"] = cycle_id, cutoff
for x in xref:
    x["cycle_id"], x["cutoff"] = cycle_id, cutoff

for table, data in (("mdm.person", people), ("mdm.household", households), ("mdm.xref", xref)):
    write(spark, data, f"lh_silver.{table}")  # noqa: F821

close(spark, notebook="nb_e1_mdm", notebook_version=NOTEBOOK_VERSION, stage="mdm",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=len(recs), target_table="lh_silver.mdm.*")
