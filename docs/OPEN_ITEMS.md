# Pendientes y supuestos (no se asumen)

Estado al 5 de octubre de 2026. «Pedido a Jhon» = el compañero que tiene la fuente recibió la solicitud por escrito; no hay respuesta registrada aquí.

La PoC ya trabaja con el esquema real de las fuentes (diccionarios y reglas entregados por Jhon). El detalle fino de las reglas está en [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md); `is_illustrative = 1` queda solo en valores de demostración.

| ID | Pendiente | Placeholder actual | Quién lo resuelve | Estado |
|---|---|---|---|---|
| G1 | Línea base manual (horas por ciclo) para el criterio de reducción ≥30 % (¿medirla sobre los mismos 500 registros?) | Columna "manual" de la Tabla 4 sin llenar | Equipo | Abierto; **aún no se ha pedido** |
| G2 | Las dos fuentes concretas y su diccionario de datos | Base maestra (`RSH_*`/`SIS_*`) e inhumados; mapeo en `img_lib.mapping` y [`NAMING.md`](NAMING.md) | Jhon | **Cerrado** con la información de Jhon; detalle en D1 y D10 de `DESIGN_DECISIONS.md` |
| G3 | Criterios de focalización | `RSH_grupo_S4 = '1. SISBEN IV - A'` (`param.targeting_criteria`) | Jhon | **Cerrado** |
| G4 | Reglas de bloqueo | `RSH_vigencia_renec NOT IN (0,12)` y existencia en inhumados (`param.block_rules`) | Jhon | **Cerrado** para estas dos reglas; semántica de nulos en D2 |
| G5 | Regla de selección de titular | Adulta, elegible (focalizada y no bloqueada), mujer, bancarizada; desempate por edad y documento (`param.holder_rule`) | Jhon | **Cerrado**; la lectura de «bancarizada» como preferencia está en D3 |
| G6 | Regla de coincidencia/supervivencia del MDM (umbrales) | Identidad por tipo + número; prevalece la fuente poblacional (`img_lib.mdm`) | Jhon | Parcial: falta confirmar umbrales de coincidencia aproximada |
| G7 | Estructura del listado por operador | 32 columnas del diccionario de dispersión, un `.xlsx` por operador (`img_lib.dispersal`) | Jhon | **Cerrado**; D5-D8 y D10 |
| G8 | Plazo y canal de cada control | 30 min en la demo (el portal exige un mínimo de 10 min en la actividad Approval) | Equipo | Abierto |
| G9 | Orden de dependencias entre cuadernos (el §23 lo marca como supuesto) | El de la Tabla 8 | Equipo | Parcial: el DAG funciona en Fabric (`runMultiple`, `nb_env_check`); falta correr la cadena completa sobre el esquema nuevo |
| G10 | ¿La Approval activity incluye aprobador y hora? | **Cerrado.** No los incluye en la salida; se registra el aprobador designado en `approvers` y la hora de término (`utcNow()`). Rechazo y vencimiento se distinguen por el mensaje. Ver `pipelines/INVENTORY.md` | Plataforma | Cerrado. Quedan por declarar en el §23: función en vista previa y premisa del equipo (solo el designado puede aprobar) **no verificada con prueba** |
| G11 | Costo operativo por ciclo (Tabla 4) | CU·s × precio de lista, declarado como estimado | Equipo | Abierto |

G2 a G7 son los 7 insumos que se le pidieron a Jhon (G2 incluye las dos fuentes y su diccionario).

## Pendientes nuevos (no numerados en el documento)
| Pendiente | Detalle | Estado |
|---|---|---|
| Importar los 23 cuadernos reales a Fabric (y volver a subir datos sintéticos, wheel y DDL de parámetros del esquema nuevo; ver `ENV_CHECK.md` §3) | Solo `nb_env_check*` están importados. Se importan como `.ipynb` (el paquete los genera con celdas separadas; el importador de `.py` los dejaba en una sola celda). Cada cuaderno necesita lakehouse por defecto, Environment y celda de parámetros marcada; se sugiere fijar el Environment como predeterminado del workspace | Abierto |
| Generar `pl_img_cycle` | 20 actividades, 4 controles y parámetros (ver `pipelines/README.md`). Falta saber cómo espera Fabric los parámetros de `TridentNotebook`: se necesita un JSON exportado de un pipeline con un cuaderno parametrizado. Se generará con un script desde la definición del DAG de `img_lib` | Abierto; se necesita ese JSON de ejemplo (no pedido a Jhon) |
| Capa de mapeo de nombres | `img_lib.mapping` renombra `RSH_*`/`SIS_*` a nombres internos entre Bronce y Plata. Ver `docs/NAMING.md` | **Hecha** (probada en local; falta correrla en Fabric) |
| Automatizar la importación de pipelines | Crear o importar pipelines (y lo estandarizable) en Fabric por importación o API para reducir el factor humano. Hoy `scripts/pipeline_tool.py` genera el JSON, pero se pega a mano en el portal. Detalle, enfoques evaluados y plan por fases en el [issue #8](https://github.com/plazasgiovanny/img-poc-fabric/issues/8) | Abierto |
| Mejorar la prueba «default lakehouse» de `nb_env_check` | No verifica el nombre: `spark.catalog.currentDatabase()` devuelve un id interno. Usar `defaultLakehouseName` del contexto | Abierto |
| Verificar la premisa de aprobación | Que otro miembro del chat no pueda aprobar al abrir el enlace | No verificado |
| Alinear `nb_record_approval` con la decisión de G10 | Hoy toma `decided_at` con `now()` dentro del cuaderno; la decisión es que el pipeline pase la hora en que termina `Approval1` (`utcNow()`) y el aprobador (`approvers`). Hay que agregar `decided_at` como parámetro y quitar el comentario `VERIFICAR (G10)` obsoleto | Abierto (cambio de código) |
