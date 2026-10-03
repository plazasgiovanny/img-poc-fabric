# nb_orq_liq — orquesta Etapa 3 (liquidación) con notebookutils.notebook.runMultiple (§18.3).
# Todos los cuadernos del DAG comparten una sola sesión Spark; cada uno recibe solo id_ciclo.
# Requiere que los cuadernos hijos usen el mismo lakehouse por defecto (lh_control) que este.

# %% Parámetros
id_ciclo = "2026-09"
pipeline_run_id = None

# %% Ejecución
from img_lib.dag import DAG_LIQ, construir_dag

dag = construir_dag(DAG_LIQ, id_ciclo, pipeline_run_id)
notebookutils.notebook.validateDAG(dag)  # noqa: F821
resultado = notebookutils.notebook.runMultiple(dag)  # noqa: F821
print(resultado)
