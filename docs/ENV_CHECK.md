# Verificación del entorno: probar en Fabric lo que hasta ahora solo se asumió

**Objetivo:** confirmar en el trial los supuestos de los que depende el resto de la PoC, antes de armar el pipeline.
Duración estimada: 2 a 3 horas. Resultado: el cuaderno `nb_env_check` deja una tabla OK/FALLA y la prueba de
aprobación responde G10.

> Repo público: **no** pegar en issues, commits ni PR el ID del tenant, correos ni capturas con datos de la cuenta.

## 0. Cuenta y trial (día 0)
1. Entrar a https://app.fabric.microsoft.com con la cuenta de trabajo o escuela (probar primero `@poligran.edu.co`).
2. Menú del perfil > **Start trial** (o "Free trial"). Si no aparece, el administrador del tenant lo desactivó:
   pedir que active «Users can try Microsoft Fabric paid features», o usar el plan alterno (tenant propio de Azure
   con correo personal y 3 usuarios en Entra ID).
3. Anotar: **¿capacidad F4 o F64?** (Administración > Capacidades). Si es F4, pedir al administrador de la
   capacidad subirla a 64 CU.
4. Los 3 integrantes deben quedar en el **mismo tenant** (si no, no podrán compartir el workspace).

## 1. Workspace, lakehouses y Environment
1. Crear el workspace **`IMG_PoC`** asignado a la capacidad Trial. (El nombre importa: los cuadernos usan
   `abfss://IMG_PoC@onelake...`.)
2. Crear 4 lakehouses **con schemas habilitados**: `lh_bronze`, `lh_silver`, `lh_gold`, `lh_control`.
3. Crear el Environment **`env_img`** > Libraries > subir `1_environment/img_lib-*.whl` > **Publish** (modo Quick).
   Los cuadernos que usan `img_lib` deben tener este Environment adjunto.

## 2. Contrato de datos y datos sintéticos
1. En `lh_control`, ejecutar `2_ddl/01_ctl_param.sql` y luego `2_ddl/02_param_illustrative.sql`
   (celda SQL de un cuaderno con `lh_control` por defecto).
2. En `lh_control` > Files, subir la carpeta `3_data/Files/synthetic` (queda `Files/synthetic/landing/cutoff1/…`
   y `Files/synthetic/ground_truth/…`). La carpeta `ground_truth` nunca la lee el pipeline; solo sirve para medir errores.

## 3. Importar cuadernos
1. Workspace > Import > Notebook: subir los `.py` de `4_notebooks/` (traen la versión de git en `NOTEBOOK_VERSION`).
2. En **cada** cuaderno: lakehouse por defecto = `lh_control`; Environment = `env_img`; marcar la primera celda de
   parámetros como **parameter cell** (menú de la celda > Toggle parameter cell). Sin esto, los argumentos de
   `runMultiple` y del pipeline no sobrescriben las variables.

## 4. Ejecutar nb_env_check
Abrir `nb_env_check` y ejecutarlo completo. Esperado: **12 OK**. El resultado queda en pantalla y en
`lh_control > Files/env_check_result.json`.

| Prueba | Si falla, significa |
|---|---|
| tablas con nombre de 3 partes | Cambiar todos los `lh_x.schema.table` por la forma que acepte el trial |
| userMetadata en DESCRIBE HISTORY | El criterio de auditoría del 100 % necesita otro mecanismo (p. ej. columna `execution_id` en cada tabla) |
| notebookutils.fs … | Ajustar `nb_e1_bronze`, `nb_06_report`, `nb_07_publish` y `nb_ctl_summary` |
| runMultiple con DAG | Revisar lakehouse por defecto de los hijos y el timeout por celda |
| escribir() con columna todo None | Revisar `img_lib.cycle.ddl_types` |

## 5. Prueba de aprobación (pendiente G10)
Crear el pipeline `pl_env_check_approval`: Notebook `nb_env_check_child_a` → **Approval** (tipo Outlook 365 o Teams,
timeout 5 min) → en éxito, Notebook `nb_env_check_child_b`; en fallo, actividad **Fail**.
Ejecutar tres veces y anotar lo que se ve en **Monitoring hub**:

| Escenario | Qué anotar |
|---|---|
| Se aprueba | ¿Existe la actividad en el trial? ¿Qué campos trae su **Output** (¿aprobador? ¿hora? ¿comentario?) |
| Se rechaza | ¿Sigue la ruta de fallo? ¿Se ve quién rechazó? |
| Nadie responde (timeout) | ¿Falla la actividad y sigue la ruta de rechazo, como pide el §19? |

**Decisión:** si la actividad no existe, no manda correo o no trae al aprobador, se usa el **plan B**
(`Until` + `Wait` + `Lookup` sobre `ctl.approvals` y `nb_approve`; ver `pipelines/README.md`).

## 6. Qué reportar
Pegar en el chat (sin IDs de tenant ni correos):
- Capacidad (F4/F64) y si el trial se activó con la cuenta institucional.
- La tabla de resultados de nb_env_check (o el JSON).
- Resultado de los tres escenarios de aprobación y los campos del Output.
- Cualquier mensaje de error completo.

Con eso se ajusta el código, se arma `pl_img_cycle` y se pasa a las corridas medidas del Experimento 2.
