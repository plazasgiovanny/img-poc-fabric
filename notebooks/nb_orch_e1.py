# nb_orch_e1 — orquesta Etapa 1 con notebookutils.notebook.runMultiple (§18.3).
# Todos los cuadernos del DAG comparten una sola sesión Spark; cada uno recibe solo cycle_id.
# Requiere que los cuadernos hijos usen el mismo lakehouse por defecto (lh_control) que este.

# %% Parámetros
cycle_id = "2026-09"
pipeline_run_id = None

# %% Ejecución
from img_lib.dag import DAG_E1, build_dag

dag = build_dag(DAG_E1, cycle_id, pipeline_run_id)
notebookutils.notebook.validateDAG(dag)  # noqa: F821
result = notebookutils.notebook.runMultiple(dag)  # noqa: F821
print(result)
