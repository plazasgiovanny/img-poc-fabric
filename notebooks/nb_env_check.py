# nb_env_check — verifica en el trial de Fabric los supuestos de los que depende el resto de la PoC.
# No es parte del pipeline. Ejecutar UNA vez, con lh_control como lakehouse por defecto y el Environment env_img adjunto.
# Cada prueba es independiente: una falla no detiene las demás. Al final deja una tabla y Files/env_check_result.json.
# Prerrequisitos: los 4 lakehouses (con schemas) creados, ddl/01_ctl_param.sql ejecutado y los cuadernos
# nb_env_check_child_a y nb_env_check_child_b importados en el mismo workspace.

# %% Parámetros
id_ciclo = "env_check"
pipeline_run_id = None

# %% Pruebas
import json

resultados = []


def prueba(nombre, fn):
    try:
        resultados.append((nombre, "OK", str(fn())[:400]))
    except Exception as e:  # noqa: BLE001 - la verificación registra cualquier falla y sigue
        resultados.append((nombre, "FALLA", f"{type(e).__name__}: {str(e)[:400]}"))


def _img_lib():
    import img_lib
    return f"img_lib {img_lib.__version__} importada desde el Environment"


def _defecto():
    return f"base de datos actual: {spark.catalog.currentDatabase()} (se espera lh_control)"  # noqa: F821


def _esquemas():
    plan = {"lh_bronce": ["bronce"], "lh_plata": ["calidad", "poblacional", "validacion", "mdm"],
            "lh_oro": ["fuentes", "cruces", "liquidacion"], "lh_control": ["ctl", "param"]}
    for lh, esquemas in plan.items():
        for e in esquemas:
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {lh}.{e}")  # noqa: F821
    return "esquemas creados con nombre de 3 partes (lakehouse.schema)"


def _tres_partes():
    spark.createDataFrame([(1, "a")], "id int, v string").write.format("delta").mode("overwrite") \
        .saveAsTable("lh_bronce.bronce.env_check")  # noqa: F821
    n = spark.table("lh_bronce.bronce.env_check").count()  # noqa: F821
    return f"escribió y leyó lh_bronce.bronce.env_check desde un cuaderno con lh_control por defecto ({n} fila)"


def _escribir_con_none():
    from img_lib.ciclo import escribir
    n = escribir(spark, [{"a": None, "b": 1}, {"a": None, "b": 2}], "lh_control.ctl.env_check_none", "overwrite")  # noqa: F821
    return f"escribir() acepta una columna todo None ({n} filas)"


def _auditoria():
    marca = "env-check-audit-1"
    spark.conf.set("spark.databricks.delta.commitInfo.userMetadata", marca)  # noqa: F821
    spark.createDataFrame([(1,)], "x int").write.format("delta").mode("overwrite") \
        .saveAsTable("lh_control.ctl.env_check_audit")  # noqa: F821
    h = spark.sql("DESCRIBE HISTORY lh_control.ctl.env_check_audit").select("version", "userMetadata").collect()  # noqa: F821
    assert any(r["userMetadata"] == marca for r in h), f"userMetadata no aparece en el historial: {h}"
    return "DESCRIBE HISTORY muestra userMetadata = id_ejecucion (la auditoría del 100 % es viable)"


def _viaje_tiempo():
    spark.createDataFrame([(2,), (3,)], "x int").write.format("delta").mode("append") \
        .saveAsTable("lh_control.ctl.env_check_audit")  # noqa: F821
    n0 = spark.sql("SELECT count(*) c FROM lh_control.ctl.env_check_audit VERSION AS OF 0").first()["c"]  # noqa: F821
    n1 = spark.table("lh_control.ctl.env_check_audit").count()  # noqa: F821
    assert (n0, n1) == (1, 3), f"VERSION AS OF 0 = {n0}, actual = {n1}"
    return "VERSION AS OF reconstruye el estado anterior (1 fila antes, 3 ahora)"


def _fs():
    base = "abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_oro.Lakehouse/Files/env_check"
    notebookutils.fs.put(f"{base}/x.txt", "hola", True)  # noqa: F821
    leido = notebookutils.fs.head(f"{base}/x.txt", 100)  # noqa: F821
    with open("/tmp/env_check_local.txt", "w") as f:
        f.write("copia")
    notebookutils.fs.cp("file:/tmp/env_check_local.txt", f"{base}/copia.txt", True)  # noqa: F821
    nombres = [x.name for x in notebookutils.fs.ls(base)]  # noqa: F821
    return f"put/head/cp/ls sobre lh_oro OK (head={leido!r}, archivos={nombres})"


def _fs_recursivo():
    base = "abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_oro.Lakehouse/Files/env_check"
    import os
    os.makedirs("/tmp/env_check_dir/sub", exist_ok=True)
    with open("/tmp/env_check_dir/sub/a.csv", "w") as f:
        f.write("a\n1\n")
    notebookutils.fs.cp("file:/tmp/env_check_dir", f"{base}/dir", True)  # noqa: F821  mismo uso que nb_07_publicar
    return f"cp recursivo de una carpeta local OK: {[x.name for x in notebookutils.fs.ls(base + '/dir')]}"  # noqa: F821


def _contexto():
    ctx = notebookutils.runtime.context  # noqa: F821
    return f"userName={ctx.get('userName')!r}; claves={sorted(ctx.keys())[:12]}"


def _ddl():
    faltan = [t for t in ("ctl.ciclo", "ctl.bitacora_ejecucion", "ctl.aprobaciones", "ctl.metricas_exp",
                          "param.operadores", "param.reglas_bloqueo")
              if not spark.catalog.tableExists(f"lh_control.{t}")]  # noqa: F821
    assert not faltan, f"faltan tablas (ejecutar ddl/01_ctl_param.sql): {faltan}"
    return "tablas de control y parámetros presentes en lh_control"


def _run_multiple():
    from img_lib.dag import construir_dag
    dag = construir_dag({"nb_env_check_child_a": [], "nb_env_check_child_b": ["nb_env_check_child_a"]}, id_ciclo, pipeline_run_id)
    notebookutils.notebook.validateDAG(dag)  # noqa: F821
    res = notebookutils.notebook.runMultiple(dag)  # noqa: F821
    return f"runMultiple con DAG de 2 cuadernos y dependencia OK: {str(res)[:250]}"


for nombre, fn in [("img_lib en el Environment", _img_lib), ("lakehouse por defecto", _defecto),
                   ("crear esquemas lakehouse.schema", _esquemas), ("tablas con nombre de 3 partes", _tres_partes),
                   ("escribir() con columna todo None", _escribir_con_none),
                   ("userMetadata en DESCRIBE HISTORY", _auditoria), ("time travel VERSION AS OF", _viaje_tiempo),
                   ("notebookutils.fs put/head/cp/ls", _fs), ("notebookutils.fs.cp recursivo", _fs_recursivo),
                   ("notebookutils.runtime.context", _contexto), ("DDL de control aplicado", _ddl),
                   ("runMultiple con DAG", _run_multiple)]:
    prueba(nombre, fn)

# %% Resultado
df = spark.createDataFrame(resultados, "prueba string, resultado string, detalle string")  # noqa: F821
df.show(truncate=False)
fallas = [r for r in resultados if r[1] != "OK"]
print(f"\n{len(resultados) - len(fallas)} OK, {len(fallas)} con falla")
notebookutils.fs.put("Files/env_check_result.json", json.dumps(  # noqa: F821
    [dict(prueba=a, resultado=b, detalle=c) for a, b, c in resultados], ensure_ascii=False, indent=2), True)
