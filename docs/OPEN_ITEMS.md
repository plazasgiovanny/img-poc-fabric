# Pendientes y supuestos (no se asumen)

Estado al 6 de octubre de 2026. «Pedido a Jhon» = el compañero que tiene la fuente recibió la solicitud por escrito; no hay respuesta registrada aquí.

La PoC ya trabaja con el esquema real de las fuentes (diccionarios y reglas entregados por Jhon). El detalle fino de las reglas está en [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md); `is_illustrative = 1` queda solo en valores de demostración.

| ID | Pendiente | Placeholder actual | Quién lo resuelve | Estado |
|---|---|---|---|---|
| G1 | Línea base manual (horas por ciclo) para el criterio de reducción ≥30 % (¿medirla sobre los mismos 500 registros?) | Columna "manual" de la Tabla 4: estimación propia del equipo ≈120 h/ciclo, declarada como tal (no es una medición) | Equipo | Abierto; sin línea base medida no se puede afirmar la reducción ≥30 % |
| G2 | Las dos fuentes concretas y su diccionario de datos | Base maestra (`RSH_*`/`SIS_*`) e inhumados; mapeo en `img_lib.mapping` y [`NAMING.md`](NAMING.md) | Jhon | **Cerrado** con la información de Jhon; detalle en D1 y D10 de `DESIGN_DECISIONS.md` |
| G3 | Criterios de focalización | `RSH_grupo_S4 = '1. SISBEN IV - A'` (`param.targeting_criteria`) | Jhon | **Cerrado** |
| G4 | Reglas de bloqueo | `RSH_vigencia_renec NOT IN (0,12)` y existencia en inhumados (`param.block_rules`) | Jhon | **Cerrado** para estas dos reglas; semántica de nulos en D2 |
| G5 | Regla de selección de titular | Adulta, elegible (focalizada y no bloqueada), mujer, bancarizada; desempate por edad y documento (`param.holder_rule`) | Jhon | **Cerrado**; la lectura de «bancarizada» como preferencia está en D3 |
| G6 | Regla de coincidencia/supervivencia del MDM (umbrales) | Identidad por tipo + número; prevalece la fuente poblacional (`img_lib.mdm`) | Jhon | Parcial: falta confirmar umbrales de coincidencia aproximada |
| G7 | Estructura del listado por operador | 32 columnas del diccionario de dispersión, un `.xlsx` por operador (`img_lib.dispersal`) | Jhon | **Cerrado**; D5-D8 y D10 |
| G8 | Plazo y canal de cada control | 30 min en la demo (el portal exige un mínimo de 10 min en la actividad Approval) | Equipo | Abierto |
| G9 | Orden de dependencias entre cuadernos (el §23 lo marca como supuesto) | El de la Tabla 8 | Equipo | **Cerrado**: la cadena completa se corrió en Fabric (ciclos `2026-10a`, `b`, `c` con orquestadores y `2026-10g` con `pl_img_cycle`) |
| G10 | ¿La Approval activity incluye aprobador y hora? | **Cerrado.** No los incluye en la salida; se registra el aprobador designado en `approvers` y la hora de término (`utcNow()`). Rechazo y vencimiento se distinguen por el mensaje. Ver `pipelines/INVENTORY.md` | Plataforma | Cerrado. Quedan por declarar en el §23: función en vista previa y premisa del equipo (solo el designado puede aprobar) **no verificada con prueba** |
| G11 | Costo operativo por ciclo (Tabla 4) | CU·s × precio de lista, declarado como estimado | Equipo | Abierto |

G2 a G7 son los 7 insumos que se le pidieron a Jhon (G2 incluye las dos fuentes y su diccionario).

## Pendientes nuevos (no numerados en el documento)
| Pendiente | Detalle | Estado |
|---|---|---|
| Importar los cuadernos reales a Fabric | Los 27 cuadernos (3 `nb_env_check*`, 23 de la cadena y `nb_measure`) están importados y ejecutados. Se importan como `.ipynb` (el paquete los genera con `scripts/notebook_tool.py`). Todo cuaderno reimportado necesita `lh_control` por defecto y cambia de ID | **Hecho** |
| Generar `pl_img_cycle` | Plantilla de 26 actividades (`pipelines/templates/pl_img_cycle.template.json`), importada y ejecutada completa con las 4 aprobaciones (ciclo `2026-10g`, 1.905 s ≈ 31,8 min; 18 actividades ejecutadas, las 8 de rechazo/fallo no se activaron). Ver `pipelines/README.md` | **Hecho**; sin verificar la ruta de rechazo/vencimiento dentro de `pl_img_cycle` |
| Capa de mapeo de nombres | `img_lib.mapping` renombra `RSH_*`/`SIS_*` a nombres internos entre Bronce y Plata. Ver `docs/NAMING.md` | **Hecha** (probada en local y corrida en Fabric dentro de la cadena) |
| Automatizar la importación de pipelines | Crear o importar pipelines (y lo estandarizable) en Fabric por importación o API para reducir el factor humano. Cubierto hasta ahora: fase 3 (cuadernos `.ipynb`) con `scripts/notebook_tool.py`; `scripts/pipeline_tool.py` cubre render, templatize e ids-from-text. Sigue manual la importación al portal y falta un script de despliegue por API. Detalle, enfoques evaluados y plan por fases en el [issue #8](https://github.com/plazasgiovanny/img-poc-fabric/issues/8) | Abierto |
| Mejorar la prueba «default lakehouse» de `nb_env_check` | No verifica el nombre: `spark.catalog.currentDatabase()` devuelve un id interno. Usar `defaultLakehouseName` del contexto | Abierto |
| Verificar la premisa de aprobación | Que otro miembro del chat no pueda aprobar al abrir el enlace | No verificado |
| Alinear `nb_record_approval` con la decisión de G10 | `decided_at` ya es parámetro (el pipeline pasa `utcNow()`). Brecha conocida: el cuaderno escribe `requested_at` con su propia hora en las filas APPROVED (posterior a `decided_at`); el tiempo de revisión se calcula como `decided_at`(APPROVED) − `requested_at`(PENDING). Falta copiar el `requested_at` de la fila PENDING | Abierto (corrección pendiente) |
| Vencimiento del trial de Fabric | Vence ≈8 de diciembre de 2026 («Queda 64 días» el 5 de octubre) | Abierto; fecha límite para las corridas pendientes |
| Experimento 1 | No ejecutado. La corrida a 10x (≈5.000 personas) sí se ejecutó: ciclo `2026-10k`, 2.033 s ≈ 33,9 min | Abierto (Experimento 1) |
