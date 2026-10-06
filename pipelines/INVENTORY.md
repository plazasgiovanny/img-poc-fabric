# Inventario de pipelines

Un pipeline de Fabric es un JSON. Aquí se versiona **sin los identificadores de tu entorno** (el repo es público) y se
rellena con un script. Así se revisa en un PR, se reproduce y no se arma a mano en el portal.

## Inventario

| Pipeline | Para qué sirve | Plantilla | Cuadernos | Conexiones | Estado |
|---|---|---|---|---|---|
| `pl_env_check_approval` | Probar la actividad **Approval** (pendiente G10) | `templates/pl_env_check_approval.template.json` | `nb_env_check_child_a`, `nb_env_check_child_b` | Teams (conexión + chat) | **Verificado** (G10 cerrado) |
| `pl_img_cycle` | Ciclo completo: ingesta, cruces, liquidación, 4 controles y publicación | `templates/pl_img_cycle.template.json` (26 actividades; diseño en [`README.md`](README.md)) | `nb_init_cycle`, `nb_orch_e1`, `nb_orch_e2`, `nb_orch_settlement`, `nb_orch_payment_lists`, `nb_ctl_summary`, `nb_record_approval`, `nb_07_publish` (sin `report_final`: `nb_06_report` corre dentro de `nb_orch_payment_lists`) | Teams (conexión + chat) | **Plantilla generada, sin probar en Fabric** |

### Qué está verificado de `pl_env_check_approval` (G10, 3 de octubre de 2026)
La plantilla se importó a Fabric sin cambios y se ejecutó tres veces:

| Corrida | Qué pasó | Cómo se distingue |
|---|---|---|
| Aprobada | `Approval1` ✓ y continúa a `NotebookB`; `Fail` no se ejecuta | salida `{"message": "Your request is approved. "}` |
| Rechazada | `Approval1` falla y se ejecuta `Fail` | `Your request is rejected. … Status code from callback: BadRequest` |
| Vencida (10 min) | `Approval1` falla y se ejecuta `Fail` | código `ActionTimedOut`, `Activity timed out` |

- La actividad **espera** la decisión (la respuesta llega por un *callback*) y su tipo es `ApprovalGroupChatMessage` (chat de grupo de Teams).
- El mensaje dinámico del `Fail` funciona: `@activity('Approval1').error.message` reproduce el mensaje de la aprobación.
- El tiempo de espera mínimo que acepta el portal es de **10 minutos**.
- "Problema de configuración de usuario" es solo la categoría con que Fabric clasifica estos fallos; no es un error de configuración.
- **Es una función en vista previa** (el nodo se titula "Aprobación (vista previa)"): Microsoft puede cambiar su comportamiento o su JSON. Por eso el plan B (`nb_approve`) se mantiene como respaldo y las plantillas facilitan corregir el formato en un solo lugar.

### Qué se registra del aprobador (decisión sobre G10)
La salida de `Approval1` **no trae** quién decidió ni cuándo; la entrada solo repite `approvers`, la lista de designados. Se decide registrar:

| Columna de `ctl.approvals` | Valor |
|---|---|
| `approver` | El valor de `approvers` configurado para ese control |
| `decided_at` | La hora en que termina `Approval1`, tomada con `utcNow()` en la actividad siguiente |
| `mechanism` | `approval_activity` |
| `decision` | `APPROVED`, `REJECTED` o `EXPIRED`, según el mensaje del error (aprobado = la actividad termina bien) |

**Cómo se decide y qué se asume.** El mensaje que llega al chat de Teams es solo un **aviso** (`[APPROVAL REQUIRED] … Approver: <correo> … View request on Fabric`): no trae botones y la decisión se toma en Fabric, en el enlace, donde el usuario ya está autenticado. El equipo parte de que solo el usuario designado en `approvers` puede aprobar, y de ahí se infiere quién aprobó. **Esa premisa del equipo no se ha verificado con una prueba** (por ejemplo, que otro miembro del chat abra el enlace e intente aprobar). Si se necesita certeza, el plan B (`nb_approve`) toma la identidad de la sesión. El documento (§23) debe declarar esta limitación y que la actividad está en vista previa.

### Qué no está verificado de `pl_img_cycle`
La plantilla no se ha importado a Fabric. Sin verificar: expresión de la descripción del Approval, literal de parámetros fijos, `@utcNow()` como parámetro y `runMultiple` dentro de un pipeline. Pasos para generarlo e importarlo: [`README.md`](README.md#obtener-los-ids-de-cuaderno-e-importar-pl_img_cycle).

## Cómo se usa

1. **Una vez:** copia `local.example.json` a `local.json` y completa tus valores (workspace, cuadernos, conexión, chat, aprobador). `local.json` está en `.gitignore`.
   Los ids de cuaderno salen de la URL de cada cuaderno en Fabric.
2. **Generar:** `python scripts/pipeline_tool.py render pl_env_check_approval` crea `output/pipelines/pl_env_check_approval.json`.
3. **Importar:** en el pipeline de Fabric, abre la vista de código JSON, pega el contenido y aplica. *No he verificado que el portal acepte un JSON sin `objectId`; si lo exige, copia ese campo del pipeline existente.*
4. **Traer cambios del portal:** si ajustaste algo en Fabric, copia el JSON de esa vista a un archivo y corre
   `python scripts/pipeline_tool.py templatize ese_archivo.json`. Quita los campos del sistema, cambia los valores reales por marcadores y **se niega** a escribir si queda algún ID o correo sin marcador.

## Marcadores de las plantillas
`{{WORKSPACE_ID}}`, `{{APPROVERS}}`, `{{TEAMS_CHAT_ID}}`, `{{TEAMS_CONNECTION_ID}}` y `{{NOTEBOOK_ID:<nombre del cuaderno>}}`.

## Pendiente
Automatizar la creación e importación de pipelines y cuadernos por API para quitar los pasos manuales: [issue #8](https://github.com/plazasgiovanny/img-poc-fabric/issues/8).

## Reglas
- Nada de GUIDs, correos ni ids de chat en `templates/` ni en `local.example.json`: lo comprueba `tests/test_pipelines.py`.
- Cada pipeline nuevo se agrega a esta tabla en el mismo PR que su plantilla.
- Nombre del pipeline: `pl_<tema>`, en inglés, igual al nombre del archivo de la plantilla.
- Un rechazo o un vencimiento de una aprobación hacen fallar a `Approval`. La ruta de fallo debe colgar de ella, no de la actividad siguiente; el test `test_rejected_or_expired_approval_goes_to_fail_not_to_notebook_b` lo protege.
