# nb_spike_hijo_a — cuaderno hijo mínimo para probar runMultiple (ver nb_spike_dia1). Mismo lakehouse por defecto que el padre.

# %% Parámetros
id_ciclo = "spike"
pipeline_run_id = None

# %% Ejecución
n = spark.range(3).count()  # noqa: F821
print(f"hijo A: id_ciclo={id_ciclo}, filas={n}")
