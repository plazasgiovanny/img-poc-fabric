# nb_env_check_child_b — depende de nb_env_check_child_a en el DAG de nb_env_check.

# %% Parámetros
cycle_id = "env_check"
pipeline_run_id = None

# %% Ejecución
print(f"child B: cycle_id={cycle_id} (runs after A)")
