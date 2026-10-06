# Verificación del entorno en Fabric: guía y resultado

**Objetivo:** confirmar en el trial los supuestos de los que depende el resto de la PoC, antes de armar el pipeline.
**Estado:** ejecutada el 3 de octubre de 2026 con resultado **13 de 13 OK** (ver [Resultado](#resultado-3-de-octubre-de-2026-13-de-13-ok)).
La guía sigue vigente para reproducir el entorno desde cero (otro workspace, otro integrante del equipo).

> Repo público: **no** pegar en issues, commits ni PR el ID del tenant, correos ni capturas con datos de la cuenta.

## Guía para reproducir el entorno

### 0. Cuenta y trial
1. Entrar a https://app.fabric.microsoft.com con la cuenta de trabajo o escuela.
2. Menú del perfil > **Start trial** (o "Free trial"). Si no aparece, el administrador del tenant lo desactivó:
   pedir que active «Users can try Microsoft Fabric paid features», o usar el plan alterno (tenant propio de Azure
   con correo personal y 3 usuarios en Entra ID).
3. Anotar si la capacidad es F4 o F64 (Administración > Capacidades). *No verificado en esta PoC cuál se obtuvo.*
4. Los 3 integrantes deben quedar en el **mismo tenant** (si no, no podrán compartir el workspace).

### 1. Workspace, lakehouses y Environment
1. Crear el workspace **`IMG_PoC`** asignado a la capacidad Trial. (El nombre importa: los cuadernos usan
   `abfss://IMG_PoC@onelake...`.)
2. Crear 4 lakehouses **con schemas habilitados**: `lh_bronze`, `lh_silver`, `lh_gold`, `lh_control`.
3. Crear el Environment **`env_img`** > Libraries > subir `1_environment/img_lib-*.whl` > **Publish** (modo Quick).
4. **Publicarlo no basta: hay que adjuntarlo** a cada cuaderno que use `img_lib` (o fijarlo como Environment
   predeterminado del workspace) y luego **reiniciar la sesión** del cuaderno. Sin eso aparece
   `ModuleNotFoundError: img_lib`.

### 2. Aplicar el DDL (desde un cuaderno, no desde un editor SQL)
El DDL de `ddl/` es **Spark SQL**. No funciona en el *SQL analytics endpoint* ni en un Warehouse (son T-SQL), y el
editor «Nueva consulta de SQL de Spark» acepta **una sola sentencia** por ejecución, mientras que cada archivo trae
varias. Por eso se ejecuta desde un **cuaderno Python**:

1. Crear un cuaderno nuevo y, en el panel Explorer, agregar `lh_control` y pulsar **Establecer como predeterminado**
   (sin lakehouse por defecto falla con *No default context found*).
2. Pegar el texto de cada archivo en una variable y ejecutar esta celda (separa por `;` y quita los comentarios `--`):

```python
def run_sql_script(script: str) -> int:
    """Ejecuta un script SQL sentencia por sentencia (Spark SQL acepta una por llamada)."""
    lines = [ln.split("--", 1)[0] for ln in script.splitlines()]   # quita comentarios
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    for statement in statements:
        spark.sql(statement)
    return len(statements)

# Pegar el contenido de ddl/01_ctl_param.sql y luego el de ddl/02_param_illustrative.sql
print(run_sql_script(ddl_01), run_sql_script(ddl_02))
```

El fragmento asume que ningún literal de texto del DDL contiene `;` ni `--`. Con el DDL actual se aplicaron
**13 sentencias** de `01_ctl_param.sql` y **7** de la versión anterior de `02_param_illustrative.sql` (la actual trae 14: un `DELETE` y un `INSERT` por tabla) (esquemas `ctl` y `param` en `lh_control`).

### 3. Datos sintéticos
En `lh_control` > Files, subir la carpeta `3_data/Files/synthetic` (queda `Files/synthetic/landing/cutoff1/…` y
`Files/synthetic/ground_truth/…`). `ground_truth` nunca la lee el pipeline; solo sirve para medir errores.

Desde la adaptación al esquema real, `landing/cutoff1/population.csv` es la **base maestra** (columnas `RSH_*`/`SIS_*`,
separador `||`, UTF-8) y `validation.csv` la **base de inhumados** (`RSH_tip_documento||RSH_num_documento||fecha_defuncion`).
Los nombres de archivo no cambian, pero el contenido sí: **volver a subir** `3_data/Files/synthetic` completa
(reemplazando) y **reaplicar `02_param_illustrative.sql`** (ahora es repetible: vacía cada tabla `param.*` antes de insertar).

Si ya se corrió algo con el esquema anterior, las tablas Delta existentes tienen otras columnas. `img_lib.cycle.write`
falla con `ValueError: columns not in table ...` si las filas traen columnas que la tabla no tiene (antes las perdía en
silencio). **Es obligatorio** borrar estas tablas una vez, desde un cuaderno con `lh_control` por defecto, antes de la
primera corrida con el esquema nuevo (`DROP TABLE IF EXISTS` no falla si alguna no existe):
```python
for t in [
    # Bronce
    "lh_bronze.bronze.population_raw", "lh_bronze.bronze.validation_raw", "lh_bronze.bronze.deliveries",
    # Plata
    "lh_silver.population.records", "lh_silver.validation.records", "lh_silver.quality.quarantine",
    "lh_silver.mdm.person", "lh_silver.mdm.household", "lh_silver.mdm.xref",
    # Oro: fuentes, cruces y liquidación
    "lh_gold.sources.population_cutoff", "lh_gold.sources.validation_cutoff",
    "lh_gold.crosschecks.stg_population", "lh_gold.crosschecks.stg_validation",
    "lh_gold.crosschecks.crosscheck_base",
    "lh_gold.settlement.targeting", "lh_gold.settlement.holders", "lh_gold.settlement.payment_method",
    "lh_gold.settlement.amount", "lh_gold.settlement.funding_source", "lh_gold.settlement.payment_list",
]:
    spark.sql(f"DROP TABLE IF EXISTS {t}")
```
Esa lista es todo lo que el código escribe en `lh_bronze`, `lh_silver` y `lh_gold` (cuadernos `nb_e1_*`, `nb_e2_*` y
`nb_00`..`nb_07`). Además, **usar un `cycle_id` nuevo** (p. ej. `2026-10a`): `nb_init_cycle` rechaza un ciclo que ya
existe en `ctl.cycle`, y las tablas de `lh_control` (`ctl.*`) no se borran.

**Listados `.xlsx`:** `img_lib.dispersal` usa `openpyxl` (importación diferida; extra opcional `img_lib[xlsx]`). El runtime
de Fabric lo suele traer, pero **no está verificado en este entorno**: antes de la corrida ejecutar `import openpyxl` en un
cuaderno con `env_img`; si falla, agregar `openpyxl` en `env_img` > Public libraries (PyPI) y publicar. Al cambiar `img_lib`
(nuevos módulos `mapping`, `dispersal`) **hay que publicar de nuevo el wheel** en `env_img` y reiniciar las sesiones.

### 4. Importar y configurar los cuadernos
1. Workspace > Import > Notebook: subir los `.ipynb` de `4_notebooks/` (traen la versión de git en `NOTEBOOK_VERSION`).
   Se importan como `.ipynb` porque el importador de `.py` de Fabric ignora los `# %%` y deja todo en una sola celda;
   en el `.ipynb` la celda de parámetros ya va separada y etiquetada como *parameters* (`scripts/notebook_tool.py`).
   Si ya importaste los `.py`, bórralos y reimporta.
   Hoy solo `nb_env_check`, `nb_env_check_child_a` y `nb_env_check_child_b` se han importado; los otros 23 no
   (ver [`OPEN_ITEMS.md`](OPEN_ITEMS.md), pendiente de importación).
2. En **cada** cuaderno: lakehouse por defecto = `lh_control`; Environment = `env_img`; verificar que la primera celda
   lleve la etiqueta **Parameters** (viene puesta). Sin esto, los argumentos de `runMultiple` y del pipeline no sobrescriben las
   variables.
3. Los cuadernos **hijos** de `runMultiple` necesitan el **mismo lakehouse por defecto** que el padre.

### 5. Ejecutar `nb_env_check`
Abrir `nb_env_check` y ejecutarlo completo (requiere el DDL aplicado y los dos hijos importados). Deja una tabla
OK/FAIL en pantalla y en `lh_control > Files/env_check_result.json`. La aprobación humana se probó aparte con el
pipeline `pl_env_check_approval` ([`pipelines/INVENTORY.md`](../pipelines/INVENTORY.md)).

## Resultado (3 de octubre de 2026): 13 de 13 OK

| # | Prueba | Qué demuestra |
|---|---|---|
| 1 | `img_lib` en el Environment | El wheel publicado y adjunto se puede importar desde el cuaderno |
| 2 | Lakehouse por defecto | Se obtiene un valor de `spark.catalog.currentDatabase()`, pero **no verifica el nombre**: Fabric devuelve un id interno, no `lh_control` (mejora pendiente: usar `defaultLakehouseName` del contexto) |
| 3 | Crear esquemas `lakehouse.schema` | `CREATE SCHEMA` con nombre de dos partes funciona en los 4 lakehouses con schemas |
| 4 | Nombres de tabla de tres partes | Un cuaderno con `lh_control` por defecto escribe y lee `lh_bronze.bronze.<tabla>`: se puede cruzar entre lakehouses sin rutas |
| 5 | `write()` con una columna toda `None` | `img_lib.cycle.write` crea la tabla aunque Spark no pueda inferir el tipo (caso `household_role`) |
| 6 | `run_log.record()` con columnas `None` | La bitácora escribe usando el esquema de la tabla existente (corrige el riesgo del PR #5) |
| 7 | `userMetadata` en `DESCRIBE HISTORY` | Cada commit Delta puede marcarse con el `execution_id`: la auditoría del 100 % es viable |
| 8 | Time travel `VERSION AS OF` | Se reconstruye el estado previo de una tabla (1 fila antes, 3 después) |
| 9 | `notebookutils.fs` put/head/cp/ls | Escritura, lectura, copia y listado en `Files/` con rutas `abfss://IMG_PoC@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/...` |
| 10 | `notebookutils.fs.cp` recursivo | Copiar una carpeta local completa a OneLake, el uso de `nb_07_publish` |
| 11 | `notebookutils.runtime.context` | El contexto de ejecución se puede leer desde el cuaderno |
| 12 | DDL de control aplicado | Las tablas `ctl.*` y `param.*` existen en `lh_control` |
| 13 | `runMultiple` con DAG | Un DAG de dos cuadernos con dependencia se valida y se ejecuta |

Lo que **no** cubre esta verificación: ninguno de los 23 cuadernos reales se ha ejecutado en Fabric, ni el rendimiento
con 500 registros. La premisa de que solo el usuario designado puede aprobar tampoco se probó.

## Errores que aparecieron y qué los causó

| Síntoma | Causa | Solución |
|---|---|---|
| «Mensaje 102, nivel 15» al correr el DDL | Se ejecutó en el *SQL analytics endpoint* (T-SQL); el DDL es Spark SQL | Ejecutarlo desde un cuaderno con Spark |
| `PARSE_SYNTAX_ERROR … extra input 'CREATE'` | El editor «Nueva consulta de SQL de Spark» acepta una sola sentencia por ejecución | Usar `run_sql_script` en un cuaderno |
| `No default context found, please attach a lakehouse before running spark sql queries with partial namespaces` | El cuaderno no tenía lakehouse por defecto | Agregar `lh_control` y pulsar **Establecer como predeterminado** |
| `ModuleNotFoundError: img_lib` | El Environment estaba sin publicar o sin adjuntar al cuaderno, o la sesión era anterior | Publicar, adjuntar y **reiniciar la sesión** |
| HTTP 400 al leer o escribir `Files/...` | Ruta relativa sin lakehouse por defecto | Fijar el lakehouse por defecto, o usar la ruta `abfss://` completa |

Después de una corrida completa de la cadena, `nb_measure` (parámetro `cycle_id`, lakehouse por defecto `lh_control`, requiere los datos sintéticos de §3) imprime el resumen del Experimento 2 y guarda `Files/measurements/<cycle_id>.json`; no escribe tablas.
