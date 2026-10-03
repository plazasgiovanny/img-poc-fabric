# nb_env_check_child_a — cuaderno hijo mínimo para probar runMultiple (ver nb_env_check). Mismo lakehouse por defecto que el padre.

# %% Parámetros
cycle_id = "env_check"
pipeline_run_id = None

# %% Ejecución
n = spark.range(3).count()  # noqa: F821
print(f"child A: cycle_id={cycle_id}, rows={n}")
