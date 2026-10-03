# nb_e2_consolidacion — Etapa 2 (§17): consolida la base de cruces, una fila por persona y ciclo. Registra HECHOS, no decisiones (Tabla 7).

# %% Parámetros (marcar como "parameters" en Fabric). El único parámetro de negocio es id_ciclo (§18.3).
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"  # se reemplaza por el tag/SHA de git al importar (ver README)

# %% Ejecución
from img_lib.ciclo import cerrar, iniciar, leer_ciclo, leer_vigentes, escribir, base_del_ciclo, filas  # noqa: F401
from img_lib.bitacora import ahora
from img_lib.cruces import construir_base, pct_coincidencia
ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
CICLO = leer_ciclo(spark, id_ciclo)  # noqa: F821
FECHA_CORTE = str(CICLO["fecha_corte"])
pob = filas(spark, "lh_oro.cruces.stg_poblacional", id_ciclo)
val = filas(spark, "lh_oro.cruces.stg_validacion", id_ciclo)
base = construir_base(
    pob, val, id_ciclo=id_ciclo, fecha_corte=FECHA_CORTE,
    version_fuentes={"poblacional": CICLO["version_fuente_poblacional"], "validacion": CICLO["version_fuente_validacion"]},
    id_ejecucion=ID_EJEC, version_cuaderno=VERSION_CUADERNO, ts=ahora())
n = escribir(spark, base, "lh_oro.cruces.base_cruces", "append")
print(f"cruces: {n} personas; % encontrado en validación = {pct_coincidencia(base):.2f}")

cerrar(spark, cuaderno="nb_e2_consolidacion", version_cuaderno=VERSION_CUADERNO, etapa="cruces",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=n, tabla_destino="lh_oro.cruces.base_cruces")
