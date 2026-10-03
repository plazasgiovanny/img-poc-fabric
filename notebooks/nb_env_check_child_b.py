# nb_env_check_child_b — depende de nb_env_check_child_a en el DAG de nb_env_check.

# %% Parámetros
id_ciclo = "env_check"
pipeline_run_id = None

# %% Ejecución
print(f"hijo B: id_ciclo={id_ciclo} (corre después de A)")
