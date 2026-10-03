# nb_ctl_resumen — §19: arma el resumen que ve el aprobador y deja la solicitud (decisión PENDIENTE) en ctl.aprobaciones. Parámetro adicional: control (C1..C4).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)
control = "C1"  # C1, C2, C3 o C4 (lo fija el pipeline)

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib import liquidacion
from img_lib.bitacora import ahora
from img_lib.cruces import pct_coincidencia
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
import json
from img_lib import controles
if control == "C1":
    entregas = [r.asDict() for r in spark.table("lh_bronce.bronce.entregas").where(f"id_ejecucion LIKE '{id_ciclo}%'").collect()]
    cuarentena = [r.asDict() for r in spark.table("lh_plata.calidad.cuarentena").where(f"id_ejecucion LIKE '{id_ciclo}%'").collect()]
    en_oro = {f: spark.table(f"lh_oro.fuentes.{f}_corte").where(f"id_ciclo = '{id_ciclo}'").count() for f in ("poblacional", "validacion")}
    res = controles.resumen_c1(entregas, cuarentena, en_oro)
elif control == "C2":
    base = base_del_ciclo(spark, id_ciclo)
    res = controles.resumen_c2(base, pct_coincidencia(base))
elif control == "C3":
    foc = filas(spark, "lh_oro.liquidacion.focalizacion", id_ciclo)
    pagos = filas(spark, "lh_oro.liquidacion.fuente_recursos", id_ciclo)
    fuentes = leer_vigentes(spark, "param.fuentes_recursos", FECHA_CORTE)
    _, estado = liquidacion.asignar_fuente_recursos([{k: p[k] for k in ("id_ciclo", "id_hogar", "id_persona", "monto", "componentes")} for p in pagos], fuentes)
    res = controles.resumen_c3(foc, pagos, estado, fuentes)
else:
    res = controles.resumen_c4(json.loads(notebookutils.fs.head(f"abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_oro.Lakehouse/Files/informes/{id_ciclo}/informe.json", 10**7)))  # noqa: F821
escribir(spark, [controles.fila_aprobacion(id_ciclo=id_ciclo, control=control, decision="PENDIENTE", aprobador=None, mecanismo="solicitud",
                                           solicitado_en=ahora(), decidido_en=None, comentario="Solicitud de aprobación", pipeline_run_id=pipeline_run_id)], "ctl.aprobaciones")

cerrar(spark, cuaderno="nb_ctl_resumen", version_cuaderno=VERSION_CUADERNO, etapa="control",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=None, tabla_destino="ctl.aprobaciones")

# exit() termina el cuaderno: va DESPUÉS de registrar la bitácora. El pipeline muestra este resumen al aprobador.
notebookutils.notebook.exit(json.dumps(res, ensure_ascii=False, default=str))  # noqa: F821
