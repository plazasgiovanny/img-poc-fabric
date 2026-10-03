# nb_env_check — verifica en el trial de Fabric los supuestos de los que depende el resto de la PoC.
# No es parte del pipeline. Ejecutar UNA vez, con lh_control como lakehouse por defecto y el Environment env_img adjunto.
# Cada prueba es independiente: una falla no detiene las demás. Al final deja una tabla y Files/env_check_result.json.
# Prerrequisitos: los 4 lakehouses (con schemas) creados, ddl/01_ctl_param.sql ejecutado y los cuadernos
# nb_env_check_child_a y nb_env_check_child_b importados en el mismo workspace.

# %% Parámetros
cycle_id = "env_check"
pipeline_run_id = None

# %% Pruebas
import json

results = []


def run_check(name, fn):
    try:
        results.append((name, "OK", str(fn())[:400]))
    except Exception as e:  # noqa: BLE001 - la verificación registra cualquier falla y sigue
        results.append((name, "FAIL", f"{type(e).__name__}: {str(e)[:400]}"))


def _img_lib():
    import img_lib
    return f"img_lib {img_lib.__version__} imported from the Environment"


def _default():
    return f"current database: {spark.catalog.currentDatabase()} (lh_control expected)"  # noqa: F821


def _schemas():
    plan = {"lh_bronze": ["bronze"], "lh_silver": ["quality", "population", "validation", "mdm"],
            "lh_gold": ["sources", "crosschecks", "settlement"], "lh_control": ["ctl", "param"]}
    for lh, schemas in plan.items():
        for e in schemas:
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {lh}.{e}")  # noqa: F821
    return "schemas created with a lakehouse.schema name"


def _three_part_names():
    spark.createDataFrame([(1, "a")], "id int, v string").write.format("delta").mode("overwrite") \
        .saveAsTable("lh_bronze.bronze.env_check")  # noqa: F821
    n = spark.table("lh_bronze.bronze.env_check").count()  # noqa: F821
    return f"wrote and read lh_bronze.bronze.env_check from a notebook whose default lakehouse is lh_control ({n} row)"


def _write_with_none():
    from img_lib.cycle import write
    n = write(spark, [{"a": None, "b": 1}, {"a": None, "b": 2}], "lh_control.ctl.env_check_none", "overwrite")  # noqa: F821
    return f"write() accepts an all-None column ({n} rows)"


def _run_log_record():
    from img_lib import run_log
    spark.sql("CREATE TABLE IF NOT EXISTS lh_control.ctl.env_check_run_log USING DELTA "  # noqa: F821
              "AS SELECT * FROM lh_control.ctl.run_log WHERE 1 = 0")
    row = run_log.event(cycle_id="env_check", execution_id="env-check-1", notebook="nb_env_check", notebook_version="dev",
                        process_stage="check", trace_event="end")   # data_source, notes, output_hash... quedan en None
    run_log.record(spark, row, "lh_control.ctl.env_check_run_log")  # noqa: F821
    n = spark.table("lh_control.ctl.env_check_run_log").count()  # noqa: F821
    return f"run_log.record() writes a row with None columns using the table schema ({n} row)"


def _audit():
    tag = "env-check-audit-1"
    spark.conf.set("spark.databricks.delta.commitInfo.userMetadata", tag)  # noqa: F821
    spark.createDataFrame([(1,)], "x int").write.format("delta").mode("overwrite") \
        .saveAsTable("lh_control.ctl.env_check_audit")  # noqa: F821
    h = spark.sql("DESCRIBE HISTORY lh_control.ctl.env_check_audit").select("version", "userMetadata").collect()  # noqa: F821
    assert any(r["userMetadata"] == tag for r in h), f"userMetadata not found in the history: {h}"
    return "DESCRIBE HISTORY shows userMetadata = execution_id (the 100 % audit is viable)"


def _time_travel():
    spark.createDataFrame([(2,), (3,)], "x int").write.format("delta").mode("append") \
        .saveAsTable("lh_control.ctl.env_check_audit")  # noqa: F821
    n0 = spark.sql("SELECT count(*) c FROM lh_control.ctl.env_check_audit VERSION AS OF 0").first()["c"]  # noqa: F821
    n1 = spark.table("lh_control.ctl.env_check_audit").count()  # noqa: F821
    assert (n0, n1) == (1, 3), f"VERSION AS OF 0 = {n0}, current = {n1}"
    return "VERSION AS OF rebuilds the previous state (1 row before, 3 now)"


def _fs():
    base = "abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_gold.Lakehouse/Files/env_check"
    notebookutils.fs.put(f"{base}/x.txt", "hello", True)  # noqa: F821
    read_back = notebookutils.fs.head(f"{base}/x.txt", 100)  # noqa: F821
    with open("/tmp/env_check_local.txt", "w") as f:
        f.write("copy")
    notebookutils.fs.cp("file:/tmp/env_check_local.txt", f"{base}/copy.txt", True)  # noqa: F821
    first_names = [x.name for x in notebookutils.fs.ls(base)]  # noqa: F821
    return f"put/head/cp/ls on lh_gold OK (head={read_back!r}, files={first_names})"


def _fs_recursive():
    base = "abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/lh_gold.Lakehouse/Files/env_check"
    import os
    os.makedirs("/tmp/env_check_dir/sub", exist_ok=True)
    with open("/tmp/env_check_dir/sub/a.csv", "w") as f:
        f.write("a\n1\n")
    notebookutils.fs.cp("file:/tmp/env_check_dir", f"{base}/dir", True)  # noqa: F821  mismo uso que nb_07_publish
    return f"recursive cp of a local folder OK: {[x.name for x in notebookutils.fs.ls(base + '/dir')]}"  # noqa: F821


def _context():
    ctx = notebookutils.runtime.context  # noqa: F821
    return f"userName={ctx.get('userName')!r}; keys={sorted(ctx.keys())[:12]}"


def _ddl():
    missing = [t for t in ("ctl.cycle", "ctl.run_log", "ctl.approvals", "ctl.exp_metrics",
                          "param.operators", "param.block_rules")
              if not spark.catalog.tableExists(f"lh_control.{t}")]  # noqa: F821
    assert not missing, f"missing tables (run ddl/01_ctl_param.sql): {missing}"
    return "control and parameter tables present in lh_control"


def _run_multiple():
    from img_lib.dag import build_dag
    dag = build_dag({"nb_env_check_child_a": [], "nb_env_check_child_b": ["nb_env_check_child_a"]}, cycle_id, pipeline_run_id)
    notebookutils.notebook.validateDAG(dag)  # noqa: F821
    res = notebookutils.notebook.runMultiple(dag)  # noqa: F821
    return f"runMultiple with a 2-notebook DAG and a dependency OK: {str(res)[:250]}"


for name, fn in [("img_lib in the Environment", _img_lib), ("default lakehouse", _default),
                   ("create lakehouse.schema schemas", _schemas), ("three-part table names", _three_part_names),
                   ("write() with an all-None column", _write_with_none),
                   ("run_log.record() with None columns", _run_log_record),
                   ("userMetadata in DESCRIBE HISTORY", _audit), ("time travel VERSION AS OF", _time_travel),
                   ("notebookutils.fs put/head/cp/ls", _fs), ("notebookutils.fs.cp recursive", _fs_recursive),
                   ("notebookutils.runtime.context", _context), ("control DDL applied", _ddl),
                   ("runMultiple with DAG", _run_multiple)]:
    run_check(name, fn)

# %% Resultado
df = spark.createDataFrame(results, "check_name string, result string, detail string")  # noqa: F821
df.show(truncate=False)
failures = [r for r in results if r[1] != "OK"]
print(f"\n{len(results) - len(failures)} OK, {len(failures)} failed")
notebookutils.fs.put("Files/env_check_result.json", json.dumps(  # noqa: F821
    [dict(check_name=a, result=b, detail=c) for a, b, c in results], ensure_ascii=False, indent=2), True)
