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
| maestro de datos (MDM) | `lh_silver.mdm` (tablas `person` y `xref`) |
| base de cruces | `lh_gold.crosschecks.crosscheck_base` |
| liquidación | esquema `settlement` (Oro) |
| control y parámetros | `lh_control`: esquemas `ctl` y `param` |

## Pipelines y plantillas
- **Pipelines:** `pl_<tema>`, en inglés y en minúsculas (`pl_env_check_approval`, `pl_img_cycle`). El nombre del pipeline es
  igual al del archivo de su plantilla: `pipelines/templates/<nombre>.template.json`.
- **Plantillas:** terminan en `.template.json` y no llevan IDs ni correos. Los valores de entorno son marcadores
  `{{WORKSPACE_ID}}`, `{{APPROVERS}}`, `{{TEAMS_CHAT_ID}}`, `{{TEAMS_CONNECTION_ID}}` y `{{NOTEBOOK_ID:<nombre del cuaderno>}}`
  (en mayúsculas, con llaves dobles). Los valores reales van en `pipelines/local.json` (ignorado por git; el modelo es `local.example.json`).
- **Actividades** de un pipeline: nombres en inglés (`NotebookA`, `Approval1`, `Fail`; en `pl_img_cycle`, `init`, `orch_e1`, `approval_c1`…).
- Cada pipeline nuevo se agrega a `pipelines/INVENTORY.md` en el mismo PR que su plantilla.

## Módulos de `img_lib`
`normalize` (normalizar), `validate` (validar), `params` (parámetros vigentes), `fingerprint` (huella SHA-256),
`run_log` (bitácora de ejecución), `mdm`, `crosschecks` (cruces), `settlement` (liquidación), `controls` (controles),
`mapping` (mapeo RSH_* y catálogos), `dispersal` (listado .xlsx), `dag`, `metrics` (métricas), `cycle` (ciclo: apertura/cierre de la ejecución y escritura Delta), `illustrative` (parámetros ilustrativos).

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

## Mapeo de la base maestra (RSH_*/SIS_*) a nombres internos
Implementado en `img_lib.mapping`. Bronce conserva los nombres crudos; Plata (`nb_e1_silver`) ya usa los internos.
| Columna de la maestra | Nombre interno | Nota |
|---|---|---|
| `RSH_id_llave_maestra` | `origin_id` | llave del registro |
| `RSH_id_hogar` | `origin_household_id` | agrupa el hogar (MDM: `household_id`) |
| `RSH_tip_parentesco` | `household_role` | catálogo 1-19 |
| `RSH_tip_documento` | `doc_type` | código de la maestra como texto: 1 CC, 2 TI, 3 CE, 4 RC, 5 DNI, 6 Pasaporte, 7 Salvoconducto, 8 PEP, 9 PPT; 0 «No tiene» es inválido |
| `RSH_num_documento` | `doc_number` | identidad = `doc_type` + `doc_number` |
| `RSH_pri_nombre`, `RSH_seg_nombre`, `RSH_pri_apellido`, `RSH_seg_apellido` | `first_name`, `second_name`, `last_name`, `second_last_name` | además `first_names` / `last_names` (partes unidas, Tabla 7) |
| `RSH_sexo_persona` | `sex` | 1 hombre, 2 mujer |
| `RSH_fec_nacimiento` | `birth_date` | ISO |
| `RSH_grupo_S4` | `sisben_group` | texto, p. ej. `1. SISBEN IV - A` |
| `RSH_vigencia_renec` | `renec_validity` | código; vacío = no bloquea |
| `SIS_edad` | `age` | |
| `SIS_cod_loc`, `SIS_nom_loc` | `locality`, `locality_name` | 1-20 y 999 «ZZ-SIN INFORMACION» |
| `SIS_bancarizado` | `banked` | 1 = tiene operador activo |
| `Cuenta1` | `operator` | DAVIPLATA, NEQUI, ALM, MOVII, EFECTY, DALE, POWWI o SIN OPERADOR |
| Inhumados: `RSH_tip_documento`, `RSH_num_documento`, `fecha_defuncion` | `doc_type`, `doc_number`, `death_date` | `origin_id` = `INH-<tipo>-<número>` |

Base de cruces: sin `address`, `sisben_subgroup` ni `survey_date` (no vienen en las columnas que usa la PoC); nuevas `sex`, `age`,
`banked`, `renec_validity`, `death_date`, `locality_name`, partes del nombre. `validation_value` = `DECEASED` cuando la persona existe en inhumados.

Reglas (`param.*`): `holder_rule.criterion` ∈ `is_adult`, `is_eligible` (elegible = focalizada y no bloqueada), `is_woman`, `is_banked`, `age`, `doc_number`;
`sort_direction` ∈ `ASC`, `DESC` (ordenan) y `REQUIRED` (filtra). Operador de regla: `=`, `!=`, `IN`, `NOT IN`.
`param.payment_list_partition.split_by` = `operator`. Causales: `RENEC_NOT_VALID`, `IN_DECEASED_REGISTRY`, `NOT_MET_SISBEN_GROUP_A`.

## Listado de dispersión (diccionario de dispersión)
Módulo `img_lib.dispersal`: 32 columnas `sdp_*` (+ `parqueadero`) en el orden del diccionario. Un `.xlsx` por `sdp_operador` en
`publication/<cycle_id>/<operador>/payment_list_<operador>.xlsx`. Tipo de documento maestra -> listado: 1 CC->3, 2 TI->2, 3 CE->4,
4 RC->1, 5 a 9 igual, sin dato -> 0 (tabla `MASTER_TO_DISPERSAL_DOC_TYPE`, con prueba).
