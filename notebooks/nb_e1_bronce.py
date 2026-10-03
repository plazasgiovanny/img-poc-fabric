# nb_e1_bronce — Etapa 1 (§16): Bronce guarda cada entrega tal como llega, sin transformarla, por
# fuente y fecha de corte, con metadatos de carga (entidad remitente, fecha de recepción, nº de
# registros, huella SHA-256). Función probatoria.
# Requiere: Environment env_img (img_lib) y lh_control como lakehouse por defecto.

# %% Parámetros (marcar esta celda como "parameters" en Fabric)
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from datetime import datetime, timezone

from pyspark.sql import functions as F

from img_lib import sha256_bytes
from img_lib.ciclo import cerrar, iniciar, leer_ciclo

ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
corte = leer_ciclo(spark, id_ciclo)["corte"]  # noqa: F821

# PENDIENTE G2: fuentes reales y entidad remitente. Genérico: poblacional + validacion.
FUENTES = {"poblacional": "ENTIDAD_REMITENTE_PENDIENTE", "validacion": "ENTIDAD_REMITENTE_PENDIENTE"}
meta = []
for fuente, remitente in FUENTES.items():
    ruta = f"Files/sinteticos/landing/{corte}/{fuente}.csv"
    crudo = spark.read.text(ruta, wholetext=True).first()[0].encode("utf-8")  # noqa: F821
    df = spark.read.option("header", True).option("inferSchema", False).csv(ruta)  # noqa: F821
    n = df.count()
    # copia inmutable del archivo, por fuente y fecha de corte
    destino = (f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_bronce.Lakehouse/"
               f"Files/entregas/{fuente}/{corte}/{fuente}.csv")
    notebookutils.fs.cp(ruta, destino, True)  # noqa: F821
    (df.withColumn("_id_ciclo", F.lit(id_ciclo)).withColumn("_fecha_corte", F.lit(corte))
       .write.format("delta").mode("append").saveAsTable(f"lh_bronce.bronce.{fuente}_raw"))
    meta.append((fuente, remitente, corte,
                 datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 f"{fuente}.csv", n, sha256_bytes(crudo), ID_EJEC))

spark.createDataFrame(  # noqa: F821
    meta, "fuente string, entidad_remitente string, fecha_corte string, fecha_recepcion string,"
          " archivo string, n_registros long, sha256 string, id_ejecucion string"
).write.format("delta").mode("append").saveAsTable("lh_bronce.bronce.entregas")

cerrar(spark, cuaderno="nb_e1_bronce", version_cuaderno=VERSION_CUADERNO, etapa="bronce",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=sum(m[5] for m in meta), tabla_destino="lh_bronce.bronce.entregas")
