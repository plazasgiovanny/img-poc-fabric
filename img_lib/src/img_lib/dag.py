"""DAG para `notebookutils.notebook.runMultiple` (§18.3): el único parámetro de cada cuaderno es
cycle_id. Todos los cuadernos del DAG comparten una sola sesión Spark. El timeout por celda de
runMultiple es de 90 s por defecto: aquí se sube explícitamente."""

CELL_TIMEOUT = 1200
TOTAL_TIMEOUT = 3600


def build_dag(activities, cycle_id, pipeline_run_id=None, cell_timeout=CELL_TIMEOUT,
                  total_timeout=TOTAL_TIMEOUT, concurrency=1):  # 1: mark_commits fija un spark.conf de sesión compartida; en paralelo se mezclaría el execution_id
    """`activities`: {notebook_name: [dependencias]}. Valida que no haya ciclos ni dependencias
    inexistentes y devuelve el JSON que espera runMultiple."""
    validate(activities)
    return {
        "activities": [
            {"name": n, "path": n, "timeoutPerCellInSeconds": cell_timeout,
             "args": {"cycle_id": cycle_id, "pipeline_run_id": pipeline_run_id},
             "dependencies": deps}
            for n, deps in activities.items()
        ],
        "timeoutInSeconds": total_timeout, "concurrency": concurrency,
    }


def validate(activities):
    for n, deps in activities.items():
        for d in deps:
            if d not in activities:
                raise ValueError(f"{n} depends on {d}, which is not in the DAG")
    pending, done_set = dict(activities), set()
    while pending:
        ready = [n for n, deps in pending.items() if all(d in done_set for d in deps)]
        if not ready:
            raise ValueError(f"cycle in the DAG among: {sorted(pending)}")
        for n in ready:
            done_set.add(n)
            del pending[n]


# Tabla 8 y §18.3: focalización -> titular -> (medio de pago || monto) -> fuente de recursos (requiere monto)
DAG_E1 = {"nb_e1_bronze": [], "nb_e1_silver": ["nb_e1_bronze"], "nb_e1_mdm": ["nb_e1_silver"],
          "nb_e1_gold": ["nb_e1_mdm"]}
DAG_E2 = {"nb_e2_crosscheck_population": [], "nb_e2_crosscheck_validation": [],
          "nb_e2_consolidation": ["nb_e2_crosscheck_population", "nb_e2_crosscheck_validation"]}
DAG_SETTLEMENT = {"nb_00_targeting": [], "nb_01_holder": ["nb_00_targeting"],
           "nb_02_payment_method": ["nb_01_holder"], "nb_03_amount": ["nb_01_holder"],
           "nb_04_funding_source": ["nb_03_amount"]}
DAG_PAYMENT_LISTS = {"nb_05_payment_lists": [], "nb_06_report": ["nb_05_payment_lists"]}
