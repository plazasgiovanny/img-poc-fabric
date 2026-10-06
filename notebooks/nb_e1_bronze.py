# nb_e1_bronze — Etapa 1 (§16): Bronce guarda cada entrega tal como llega (columnas RSH_*/SIS_* crudas, CSV separado por '||'), sin transformarla, por
# fuente y fecha de corte, con metadatos de carga (entidad remitente, fecha de recepción, nº de
# registros, huella SHA-256). Función probatoria.
# Requiere: Environment env_img (img_lib) y lh_control como lakehouse por defecto.

# %% Parámetros (marcar esta celda como "parameters" en Fabric)
cycle_id = "2026-09"
execution_id = None
pipeline_run_id = None
NOTEBOOK_VERSION = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from datetime import datetime, timezone

from pyspark.sql import functions as F

from img_lib import sha256_bytes
from img_lib.cycle import close, start, read_cycle

EXEC_ID, T0 = start(spark, cycle_id, execution_id)  # noqa: F821
cutoff = read_cycle(spark, cycle_id)["cutoff"]  # noqa: F821

# Fuentes: population = base maestra poblacional; validation = base de inhumados. Entidad remitente por confirmar.
SOURCES = {"population": "SENDER_ENTITY_PENDING", "validation": "SENDER_ENTITY_PENDING"}
meta = []
for source, sender in SOURCES.items():
    path = f"Files/synthetic/landing/{cutoff}/{source}.csv"
    raw_bytes = spark.read.text(path, wholetext=True).first()[0].encode("utf-8")  # noqa: F821
    df = (spark.read.option("header", True).option("inferSchema", False)  # noqa: F821
           .option("sep", "||").option("encoding", "UTF-8").csv(path))
    n = df.count()
    # copia inmutable del archivo, por fuente y fecha de corte
    destination = (f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_bronze.Lakehouse/"
               f"Files/deliveries/{source}/{cutoff}/{source}.csv")
    notebookutils.fs.cp(path, destination, True)  # noqa: F821
    (df.withColumn("_cycle_id", F.lit(cycle_id)).withColumn("_cutoff_date", F.lit(cutoff))
       .write.format("delta").mode("append").saveAsTable(f"lh_bronze.bronze.{source}_raw"))
    meta.append((source, sender, cutoff,
                 datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 f"{source}.csv", n, sha256_bytes(raw_bytes), EXEC_ID))

spark.createDataFrame(  # noqa: F821
    meta, "source string, sender_entity string, cutoff_date string, received_date string,"
          " file string, n_records long, sha256 string, execution_id string"
).write.format("delta").mode("append").saveAsTable("lh_bronze.bronze.deliveries")

close(spark, notebook="nb_e1_bronze", notebook_version=NOTEBOOK_VERSION, stage="bronze",  # noqa: F821
       cycle_id=cycle_id, execution_id=EXEC_ID, t0=T0, pipeline_run_id=pipeline_run_id,
       records_processed=sum(m[5] for m in meta), target_table="lh_bronze.bronze.deliveries")
