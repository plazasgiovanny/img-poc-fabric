"""DAG para `notebookutils.notebook.runMultiple` (§18.3): el único parámetro de cada cuaderno es
id_ciclo. Todos los cuadernos del DAG comparten una sola sesión Spark. El timeout por celda de
runMultiple es de 90 s por defecto: aquí se sube explícitamente."""

TIMEOUT_CELDA = 1200
TIMEOUT_TOTAL = 3600


def construir_dag(actividades, id_ciclo, pipeline_run_id=None, timeout_celda=TIMEOUT_CELDA,
                  timeout_total=TIMEOUT_TOTAL, concurrencia=2):
    """`actividades`: {nombre_cuaderno: [dependencias]}. Valida que no haya ciclos ni dependencias
    inexistentes y devuelve el JSON que espera runMultiple."""
    validar(actividades)
    return {
        "activities": [
            {"name": n, "path": n, "timeoutPerCellInSeconds": timeout_celda,
             "args": {"id_ciclo": id_ciclo, "pipeline_run_id": pipeline_run_id},
             "dependencies": deps}
            for n, deps in actividades.items()
        ],
        "timeoutInSeconds": timeout_total, "concurrency": concurrencia,
    }


def validar(actividades):
    for n, deps in actividades.items():
        for d in deps:
            if d not in actividades:
                raise ValueError(f"{n} depende de {d}, que no está en el DAG")
    pendientes, hechos = dict(actividades), set()
    while pendientes:
        listos = [n for n, deps in pendientes.items() if all(d in hechos for d in deps)]
        if not listos:
            raise ValueError(f"ciclo en el DAG entre: {sorted(pendientes)}")
        for n in listos:
            hechos.add(n)
            del pendientes[n]


# Tabla 8 y §18.3: focalización -> titular -> (medio de pago || monto) -> fuente de recursos (requiere monto)
DAG_E1 = {"nb_e1_bronce": [], "nb_e1_plata": ["nb_e1_bronce"], "nb_e1_mdm": ["nb_e1_plata"],
          "nb_e1_oro": ["nb_e1_mdm"]}
DAG_E2 = {"nb_e2_cruce_poblacional": [], "nb_e2_cruce_validacion": [],
          "nb_e2_consolidacion": ["nb_e2_cruce_poblacional", "nb_e2_cruce_validacion"]}
DAG_LIQ = {"nb_00_focalizacion": [], "nb_01_titular": ["nb_00_focalizacion"],
           "nb_02_medio_pago": ["nb_01_titular"], "nb_03_monto": ["nb_01_titular"],
           "nb_04_fuente_recursos": ["nb_03_monto"]}
DAG_LISTADOS = {"nb_05_listados": [], "nb_06_informe": ["nb_05_listados"]}
