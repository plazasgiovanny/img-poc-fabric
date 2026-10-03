# nb_06_informe — Tabla 8: informe de generación (lee la bitácora y las aprobaciones). Idempotente: se ejecuta antes de C4 y al cierre, ya con C4.

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
import json
base = base_del_ciclo(spark, id_ciclo)
foc = filas(spark, "lh_oro.liquidacion.focalizacion", id_ciclo)
tit = filas(spark, "lh_oro.liquidacion.titulares", id_ciclo)
pagos = filas(spark, "lh_oro.liquidacion.fuente_recursos", id_ciclo)
sabana = filas(spark, "lh_oro.liquidacion.listado", id_ciclo)
aprob = [{k: str(v) for k, v in r.items()} for r in filas(spark, "ctl.aprobaciones", id_ciclo)]
versiones = {r["cuaderno"]: r["version_cuaderno"] for r in filas(spark, "ctl.bitacora_ejecucion", id_ciclo)}
param = {t: leer_vigentes(spark, f"param.{t}", FECHA_CORTE) for t in
         ("criterios_focalizacion", "reglas_bloqueo", "regla_titular", "operadores", "montos", "fuentes_recursos")}
informe = liquidacion.armar_informe(
    id_ciclo=id_ciclo, fecha_corte=FECHA_CORTE,
    version_fuentes={"poblacional": CICLO["version_fuente_poblacional"], "validacion": CICLO["version_fuente_validacion"]},
    parametros_aplicados=param, versiones_cuadernos=versiones, base=base, focalizacion=foc, titulares=tit,
    pagos=pagos, sabana=sabana, aprobaciones=aprob)
ruta = f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_oro.Lakehouse/Files/informes/{id_ciclo}/informe.json"
notebookutils.fs.put(ruta, json.dumps(informe, ensure_ascii=False, indent=2, default=str), True)  # noqa: F821
n = len(sabana)

cerrar(spark, cuaderno="nb_06_informe", version_cuaderno=VERSION_CUADERNO, etapa="informe",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.Files/informes")
