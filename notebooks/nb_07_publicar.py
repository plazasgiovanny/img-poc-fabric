# nb_07_publicar — Adaptación de la PoC al §18.4: publica en OneLake Files (carpeta por ciclo y operador, con huella SHA-256). Producción: Azure Storage con política de inmutabilidad. SOLO se ejecuta si C1 a C4 están APROBADOS.

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib import liquidacion
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
from img_lib import controles
aprob = filas(spark, "ctl.aprobaciones", id_ciclo)
aprob = [{**a, "decidido_en": str(a["decidido_en"] or "")} for a in aprob]
if not controles.todas_aprobadas(aprob, id_ciclo):
    raise RuntimeError("No se publica: faltan controles aprobados (vencido o ausente = rechazo, §19)")
base = base_del_ciclo(spark, id_ciclo)
pagos = filas(spark, "lh_oro.liquidacion.fuente_recursos", id_ciclo)
mp = filas(spark, "lh_oro.liquidacion.medio_pago", id_ciclo)
_, archivos = liquidacion.generar_listados(pagos, mp, base)
tmp = "/tmp/publicacion"
manifiesto = liquidacion.publicar(archivos, tmp, id_ciclo)
destino = f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_oro.Lakehouse/Files/publicacion/{id_ciclo}"
notebookutils.fs.cp(f"file:{tmp}/{id_ciclo}", destino, True)  # noqa: F821  copia recursiva a lh_oro
n = sum(m["filas"] for m in manifiesto)

cerrar(spark, cuaderno="nb_07_publicar", version_cuaderno=VERSION_CUADERNO, etapa="publicacion",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.Files/publicacion")
