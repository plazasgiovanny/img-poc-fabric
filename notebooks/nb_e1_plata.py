# nb_e1_plata — Etapa 1 (§16): normaliza tipos/números de documento, nombres, fechas y localidades;
# elimina duplicados exactos DENTRO de cada fuente; aplica reglas de calidad. Lo que incumple va a
# calidad.cuarentena con la causa del rechazo. (PoC: una sola función para ambas fuentes.)

# %% Parámetros
id_ciclo = "2026-09"
id_ejecucion = None
pipeline_run_id = None
VERSION_CUADERNO = "dev"

# %% Ejecución
from datetime import date

from img_lib.ciclo import cerrar, escribir, iniciar, leer_ciclo
from img_lib.validar import validar_registro

ID_EJEC, T0 = iniciar(spark, id_ciclo, id_ejecucion)  # noqa: F821
corte = leer_ciclo(spark, id_ciclo)["corte"]  # noqa: F821
hoy = date.today()
total, errores_dup = 0, 0

for fuente in ("poblacional", "validacion"):
    filas = [r.asDict() for r in spark.table(f"lh_bronce.bronce.{fuente}_raw")  # noqa: F821
             .where(f"_id_ciclo = '{id_ciclo}' AND _fecha_corte = '{corte}'").collect()]
    ok, rechazados, vistos = [], [], set()
    for r in filas:
        reg, causas = validar_registro(r, hoy=hoy)
        if causas:
            rechazados.append({"fuente": fuente, "id_origen": r["id_origen"], "regla": ";".join(causas),
                               "causa": ";".join(causas), "valor": str(r.get("num_doc")),
                               "id_ejecucion": ID_EJEC})
            continue
        llave = (reg["tipo_doc"], reg["num_doc"], reg["nombres"], reg["apellidos"], reg["fecha_nacimiento"])
        if llave in vistos:  # duplicado exacto dentro de la fuente
            errores_dup += 1
            continue
        vistos.add(llave)
        reg["id_ciclo"], reg["corte"] = id_ciclo, corte
        ok.append(reg)
    total += len(filas)
    escribir(spark, ok, f"lh_plata.{fuente}.registros")  # noqa: F821
    escribir(spark, rechazados, "lh_plata.calidad.cuarentena")  # noqa: F821

cerrar(spark, cuaderno="nb_e1_plata", version_cuaderno=VERSION_CUADERNO, etapa="plata",  # noqa: F821
       id_ciclo=id_ciclo, id_ejecucion=ID_EJEC, t0=T0, pipeline_run_id=pipeline_run_id,
       num_registros_procesados=total, num_errores_duplicidad=errores_dup,
       tabla_destino="lh_plata.*.registros")
