# nb_measure — Experimento 2 (§7): mide un ciclo ya ejecutado (tiempos, embudo, calidad contra la verdad conocida, trazabilidad,
# aprobación humana), imprime un resumen y guarda Files/measurements/<cycle_id>.json en lh_control. SOLO LEE: no escribe tablas Delta.
# Requiere lh_control como lakehouse por defecto (ctl.* y Files/synthetic/ground_truth).

# %% Parámetros (marcar esta celda como "parameters" en Fabric)
cycle_id = "2026-09"
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
import json

from img_lib import measure
from img_lib.cycle import read_active, read_cycle, rows

CYCLE = read_cycle(spark, cycle_id)  # noqa: F821
cutoff = CYCLE["cutoff"]
CUTOFF_DATE = str(CYCLE["cutoff_date"])
like = f"execution_id LIKE '{cycle_id}%'"


def dicts(df):
    return [{k: (str(v) if hasattr(v, "isoformat") else v) for k, v in r.asDict().items()} for r in df.collect()]


run_log = rows(spark, "ctl.run_log", cycle_id)  # noqa: F821
approvals = rows(spark, "ctl.approvals", cycle_id)  # noqa: F821
deliveries = dicts(spark.table("lh_bronze.bronze.deliveries").where(like))  # noqa: F821
quarantine = (dicts(spark.table("lh_silver.quality.quarantine").where(like))  # noqa: F821
              if spark.catalog.tableExists("lh_silver.quality.quarantine") else [])  # noqa: F821
silver = {s: spark.table(f"lh_silver.{s}.records").where(f"cycle_id = '{cycle_id}'").count()  # noqa: F821
          for s in ("population", "validation")}
xref = rows(spark, "lh_silver.mdm.xref", cycle_id)  # noqa: F821
base = rows(spark, "lh_gold.crosschecks.crosscheck_base", cycle_id)  # noqa: F821
tgt = rows(spark, "lh_gold.settlement.targeting", cycle_id)  # noqa: F821
hld = rows(spark, "lh_gold.settlement.holders", cycle_id)  # noqa: F821
pay = rows(spark, "lh_gold.settlement.funding_source", cycle_id)  # noqa: F821

# Calidad: verdad conocida del generador (CSV con ',' como separador, ver generator.write)
gt_path = f"Files/synthetic/ground_truth/{cutoff}/ground_truth.csv"
try:
    gt = dicts(spark.read.option("header", True).option("sep", ",").csv(gt_path))  # noqa: F821
    block_reasons = [b["reason"] for b in read_active(spark, "param.block_rules", CUTOFF_DATE)]  # noqa: F821
    quality = measure.quality(gt, xref, tgt, hld, [(q["source"], q["origin_id"]) for q in quarantine], block_reasons)
except Exception as e:  # noqa: BLE001
    quality = {"error": f"no se pudo leer/calcular la verdad conocida en {gt_path}: {type(e).__name__}: {e}"}

# Trazabilidad: DESCRIBE HISTORY de las tablas del ciclo (userMetadata = execution_id)
TABLES = (["lh_bronze.bronze.deliveries", "lh_bronze.bronze.population_raw", "lh_bronze.bronze.validation_raw",
           "lh_silver.population.records", "lh_silver.validation.records", "lh_silver.quality.quarantine",
           "lh_silver.mdm.person", "lh_silver.mdm.household", "lh_silver.mdm.xref",
           "lh_gold.sources.population_cutoff", "lh_gold.sources.validation_cutoff", "lh_gold.crosschecks.crosscheck_base"]
          + [f"lh_gold.settlement.{t}" for t in ("targeting", "holders", "payment_method", "amount", "funding_source", "payment_list")]
          + ["ctl.run_log", "ctl.approvals"])
commits, skipped = [], []
for t in TABLES:
    try:
        for r in spark.sql(f"DESCRIBE HISTORY {t}").select("version", "timestamp", "userMetadata").collect():  # noqa: F821
            commits.append({"table": t, "version": r["version"], "timestamp": str(r["timestamp"]), "userMetadata": r["userMetadata"]})
    except Exception:  # noqa: BLE001 - la tabla puede no existir en este ciclo
        skipped.append(t)
trace = measure.traceability(commits, run_log)
trace["tables_without_history"] = skipped

result = {"cycle_id": cycle_id, "cutoff": cutoff, "notebook_version": NOTEBOOK_VERSION,
          "timings": measure.timings(run_log),
          "funnel": measure.funnel(deliveries=deliveries, silver_by_source=silver, quarantine=quarantine,
                                   universe=len(base), targeting=tgt, holders=hld, payments=pay),
          "quality": quality, "traceability": trace, "human_approval": measure.human_approval(approvals)}

print(measure.render(result))
path = f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_control.Lakehouse/Files/measurements/{cycle_id}.json"
notebookutils.fs.put(path, json.dumps(result, ensure_ascii=False, indent=2, default=str), True)  # noqa: F821
print(f"JSON: {path}")
