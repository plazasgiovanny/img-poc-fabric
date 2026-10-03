# nb_env_check_child_a — cuaderno hijo mínimo para probar runMultiple (ver nb_env_check). Mismo lakehouse por defecto que el padre.

# %% Parámetros
id_ciclo = "env_check"
pipeline_run_id = None

# %% Ejecución
n = spark.range(3).count()  # noqa: F821
print(f"hijo A: id_ciclo={id_ciclo}, filas={n}")
