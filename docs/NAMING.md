# Convención de nombres y correspondencia con el documento

**Regla del repositorio:** todo lo que es código está en inglés (archivos, módulos, funciones, variables, tablas,
columnas, esquemas, valores como `APPROVED`). Lo único en español son los **comentarios**, los **docstrings** y la
**documentación** (README, `docs/`, guías). Los datos sintéticos de ejemplo (nombres de personas, direcciones)
conservan el formato colombiano.

El documento del caso (`Caso_Analisis_IMG_Automatizacion_v2`) usa términos en español. Estas tablas permiten pasar de
uno a otro sin perder la trazabilidad.

## Cuadernos (Tabla 8 y orquestación)
| Documento / concepto | Repositorio |
|---|---|
| `nb_00_focalizacion` | `nb_00_targeting` |
| `nb_01_titular` | `nb_01_holder` |
| `nb_02_medio_pago` | `nb_02_payment_method` |
| `nb_03_monto` | `nb_03_amount` |
| `nb_04_fuente_recursos` | `nb_04_funding_source` |
| `nb_05_listados` | `nb_05_payment_lists` |
| `nb_06_informe` | `nb_06_report` |
| publicación en el contenedor (§18.4, adaptada a OneLake) | `nb_07_publish` |
| ingesta Bronce / Plata / MDM / Oro | `nb_e1_bronze`, `nb_e1_silver`, `nb_e1_mdm`, `nb_e1_gold` |
| cruces por familia y consolidación | `nb_e2_crosscheck_population`, `nb_e2_crosscheck_validation`, `nb_e2_consolidation` |
| apertura del ciclo | `nb_init_cycle` |
| resumen y registro de los controles | `nb_ctl_summary`, `nb_record_approval`, `nb_approve` (plan B) |
| orquestadores `runMultiple` | `nb_orch_e1`, `nb_orch_e2`, `nb_orch_settlement`, `nb_orch_payment_lists` |
| verificación del entorno | `nb_env_check` (+ `_child_a`, `_child_b`) |

## Capas y esquemas
| Documento | Repositorio |
|---|---|
| Bronce, Plata, Oro | `lh_bronze`, `lh_silver`, `lh_gold` (esquema `bronze` en el primero) |
| cuarentena | `lh_silver.quality.quarantine` |
| fuentes poblacionales / de validación | esquemas `population`, `validation` (Plata) y `sources` (Oro) |
| base de cruces | `lh_gold.crosschecks.crosscheck_base` |
| liquidación | esquema `settlement` (Oro) |
| control y parámetros | `lh_control`: esquemas `ctl` y `param` |

## Módulos de `img_lib`
`normalize` (normalizar), `validate` (validar), `params` (parámetros vigentes), `fingerprint` (huella SHA-256),
`run_log` (bitácora de ejecución), `mdm`, `crosschecks` (cruces), `settlement` (liquidación), `controls` (controles),
`dag`, `metrics` (métricas), `cycle` (ciclo), `illustrative` (parámetros ilustrativos).

## Base de cruces (Tabla 7)
| Grupo del documento | Columnas |
|---|---|
| Ciclo | `cycle_id`, `cutoff_date`, `population_source_version`, `validation_source_version` |
| Persona | `person_id`, `doc_type`, `doc_number`, `first_names`, `last_names`, `birth_date` |
| Hogar y ubicación | `household_id`, `household_role`, `locality`, `address` |
| Clasificación Sisbén IV | `sisben_group`, `sisben_subgroup`, `survey_date` |
| Marcas de validación | `validation_found`, `validation_value`, `validation_cutoff_date` |
| Datos financieros | `operator`, `product_type`, `product_status` |
| Trazabilidad | `execution_id`, `notebook_version`, `process_ts` |

## Bitácora de ejecución (Instrumento A, Tabla 2)
| Instrumento A | Columna |
|---|---|
| ID_lote | `batch_id` |
| Fecha_ciclo | `cycle_date` |
| Hora_inicio / Hora_fin | `start_time` / `end_time` |
| Num_registros_procesados | `records_processed` |
| Horas_hombre_manual | `manual_labor_hours` |
| Num_errores_duplicidad | `duplicate_errors` |
| Etapa_proceso | `process_stage` |
| Modo_procesamiento | `processing_mode` |
| Evento_trazabilidad | `trace_event` |
| Fuente_dato | `data_source` |
| Observaciones | `notes` |

## Valores
| Español | Código |
|---|---|
| APROBADO, RECHAZADO, VENCIDO, PENDIENTE | `APPROVED`, `REJECTED`, `EXPIRED`, `PENDING` |
| VIVO, FALLECIDO | `ALIVE`, `DECEASED` |
| encontrado en validación: SI / NO | `YES` / `NO` |
| parámetros ilustrativos | columna `is_illustrative = 1` |
| `id_ciclo` (único parámetro de los cuadernos, §18.3) | `cycle_id` |
| `direccion` de la regla de titular (sentido ASC/DESC) | `sort_direction` (distinto de `address`, la dirección de residencia) |
| `orden` de la regla de titular | `rank` |
| `por` de la partición de listados | `split_by` |

## Fuentes reales (pendiente G2)
Los nombres de campo de las fuentes reales (por ejemplo los de Sisbén IV) serán en español. Cuando el equipo entregue el
diccionario, se agrega una capa de mapeo entre Bronce y Plata que renombre cada columna real al nombre interno de arriba;
los cuadernos y `img_lib` no cambian.
