# Pendientes y supuestos (no se asumen)

Estado al 3 de octubre de 2026. «Pedido a Jhon» = el compañero que tiene la fuente recibió la solicitud por escrito; no hay respuesta registrada aquí.

Nada de lo siguiente está definido en el documento v2 ni lo ha confirmado el equipo. Mientras tanto la PoC usa
un placeholder parametrizado con `is_illustrative = 1`, visible en el informe de generación.

| ID | Pendiente | Placeholder actual | Quién lo resuelve | Estado |
|---|---|---|---|---|
| G1 | Línea base manual (horas por ciclo) para el criterio de reducción ≥30 % (¿medirla sobre los mismos 500 registros?) | Columna "manual" de la Tabla 4 sin llenar | Equipo | Abierto; **aún no se ha pedido** |
| G2 | Las dos fuentes concretas y su diccionario de datos (campos, tipos, formato, separador, codificación) | `population` / `validation`, esquema provisional en `generator/` | Jhon | Abierto; **pedido a Jhon** |
| G3 | Criterios de focalización | `TARGETING_PLACEHOLDER_01` | Jhon (manual SDIS) | Abierto; **pedido a Jhon** |
| G4 | Reglas de bloqueo (el doc menciona 15, no las enumera); se piden 1 o 2 reales con su causal | `BLOCK_PLACEHOLDER_01/02` | Jhon | Abierto; **pedido a Jhon** |
| G5 | Regla de selección de titular | Orden ilustrativo en `param.holder_rule` | Jhon | Abierto; **pedido a Jhon** |
| G6 | Regla de coincidencia/supervivencia del MDM (umbrales) | Documento exacto; prevalece la fuente poblacional (`img_lib.mdm`) | Jhon | Abierto; **pedido a Jhon** |
| G7 | Estructura del listado por operador | Columnas de la Tabla 7 | Jhon | Abierto; **pedido a Jhon** |
| G8 | Plazo y canal de cada control | 30 min en la demo (el portal exige un mínimo de 10 min en la actividad Approval) | Equipo | Abierto |
| G9 | Orden de dependencias entre cuadernos (el §23 lo marca como supuesto) | El de la Tabla 8 | Equipo | Abierto; el DAG con dependencias funciona en Fabric (`runMultiple`, `nb_env_check`) |
| G10 | ¿La Approval activity incluye aprobador y hora? | **Cerrado.** No los incluye en la salida; se registra el aprobador designado en `approvers` y la hora de término (`utcNow()`). Rechazo y vencimiento se distinguen por el mensaje. Ver `pipelines/INVENTORY.md` | Plataforma | Cerrado. Quedan por declarar en el §23: función en vista previa y premisa del equipo (solo el designado puede aprobar) **no verificada con prueba** |
| G11 | Costo operativo por ciclo (Tabla 4) | CU·s × precio de lista, declarado como estimado | Equipo | Abierto |

G2 a G7 son los 7 insumos que se le pidieron a Jhon (G2 incluye las dos fuentes y su diccionario).

## Pendientes nuevos (no numerados en el documento)
| Pendiente | Detalle | Estado |
|---|---|---|
| Importar los 23 cuadernos reales a Fabric | Solo `nb_env_check*` están importados. Duda abierta: si Fabric parte los `.py` en celdas por `# %%` (no verificado; nadie lo ha reportado); si no, generar `.ipynb` en el paquete. Cada cuaderno necesita lakehouse por defecto, Environment y celda de parámetros marcada; se sugiere fijar el Environment como predeterminado del workspace | Abierto |
| Generar `pl_img_cycle` | 20 actividades, 4 controles y parámetros (ver `pipelines/README.md`). Falta saber cómo espera Fabric los parámetros de `TridentNotebook`: se necesita un JSON exportado de un pipeline con un cuaderno parametrizado. Se generará con un script desde la definición del DAG de `img_lib` | Abierto; se necesita ese JSON de ejemplo (no pedido a Jhon) |
| Capa de mapeo de nombres | Renombrar las columnas reales (en español) a los nombres internos entre Bronce y Plata; depende de G2. Ver `docs/NAMING.md` | No construida |
| Automatizar la importación de pipelines | Crear o importar pipelines (y lo estandarizable) en Fabric por importación o API para reducir el factor humano. Hoy `scripts/pipeline_tool.py` genera el JSON, pero se pega a mano en el portal | Abierto |
| Mejorar la prueba «default lakehouse» de `nb_env_check` | No verifica el nombre: `spark.catalog.currentDatabase()` devuelve un id interno. Usar `defaultLakehouseName` del contexto | Abierto |
| Verificar la premisa de aprobación | Que otro miembro del chat no pueda aprobar al abrir el enlace | No verificado |
