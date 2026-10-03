# nb_04_fuente_recursos — Tabla 8: fuente asignada a cada pago y saldo por fuente (requiere el monto). ILUSTRATIVO.

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
mon = filas(spark, "lh_oro.liquidacion.monto", id_ciclo)
fuentes = leer_vigentes(spark, "param.fuentes_recursos", FECHA_CORTE)
pagos, estado = liquidacion.asignar_fuente_recursos(mon, fuentes)
n = escribir(spark, pagos, "lh_oro.liquidacion.fuente_recursos")
print(f"saldo por fuente: {estado['saldo']}; pagos sobre el techo: {estado['pagos_sobre_techo']}")

cerrar(spark, cuaderno="nb_04_fuente_recursos", version_cuaderno=VERSION_CUADERNO, etapa="liquidacion",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.liquidacion.fuente_recursos")
