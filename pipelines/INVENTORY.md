# Inventario de pipelines

Un pipeline de Fabric es un JSON. Aquí se versiona **sin los identificadores de tu entorno** (el repo es público) y se
rellena con un script. Así se revisa en un PR, se reproduce y no se arma a mano en el portal.

## Inventario

| Pipeline | Para qué sirve | Plantilla | Cuadernos | Conexiones | Estado |
|---|---|---|---|---|---|
| `pl_env_check_approval` | Probar la actividad **Approval** (pendiente G10) | `templates/pl_env_check_approval.template.json` | `nb_env_check_child_a`, `nb_env_check_child_b` | Teams (conexión + chat) | **En prueba** |
| `pl_img_cycle` | Ciclo completo: ingesta, cruces, liquidación, 4 controles y publicación | Pendiente; el diseño está en [`README.md`](README.md) | Los 23 cuadernos | Teams u Outlook, o el plan B | **Planeado** |

### Qué está verificado de `pl_env_check_approval`
- La actividad `Approval` **existe** en el trial y **espera** la decisión (`operationType: ApprovalGroupChatMessage`, aprobación por un chat de grupo de Teams).
- **Rechazo:** `Approval1` falla con `Your request is rejected. Status code from callback: BadRequest`. Fabric lo clasifica como "Problema de configuración de usuario"; es solo la categoría, no un error de configuración.
- El tiempo de espera mínimo que acepta el portal es de **10 minutos**.
- **Pendiente:** la salida de una corrida aprobada (¿trae quién aprobó y cuándo?), el texto del error al vencer el plazo, y si `@activity('Approval1').error.message` funciona en el mensaje del `Fail`.
- La plantilla corregida (el `Fail` cuelga de `Approval1`, no de `NotebookB`) **todavía no se ha importado** a Fabric.

### Qué no está verificado de `pl_img_cycle`
Cómo espera Fabric los parámetros de una actividad de cuaderno (`TridentNotebook`) y el comportamiento exacto de `runMultiple` dentro de un pipeline. Se generará con un script a partir de la definición del DAG de `img_lib`, una vez resueltos el G10 y el formato de parámetros.

## Cómo se usa

1. **Una vez:** copia `local.example.json` a `local.json` y completa tus valores (workspace, cuadernos, conexión, chat, aprobador). `local.json` está en `.gitignore`.
   Los ids de cuaderno salen de la URL de cada cuaderno en Fabric.
2. **Generar:** `python scripts/pipeline_tool.py render pl_env_check_approval` crea `output/pipelines/pl_env_check_approval.json`.
3. **Importar:** en el pipeline de Fabric, abre la vista de código JSON, pega el contenido y aplica. *No he verificado que el portal acepte un JSON sin `objectId`; si lo exige, copia ese campo del pipeline existente.*
4. **Traer cambios del portal:** si ajustaste algo en Fabric, copia el JSON de esa vista a un archivo y corre
   `python scripts/pipeline_tool.py templatize ese_archivo.json`. Quita los campos del sistema, cambia los valores reales por marcadores y **se niega** a escribir si queda algún ID o correo sin marcador.

## Marcadores de las plantillas
`{{WORKSPACE_ID}}`, `{{APPROVERS}}`, `{{TEAMS_CHAT_ID}}`, `{{TEAMS_CONNECTION_ID}}` y `{{NOTEBOOK_ID:<nombre del cuaderno>}}`.

## Reglas
- Nada de GUIDs, correos ni ids de chat en `templates/` ni en `local.example.json`: lo comprueba `tests/test_pipelines.py`.
- Cada pipeline nuevo se agrega a esta tabla en el mismo PR que su plantilla.
- Nombre del pipeline: `pl_<tema>`, en inglés, igual al nombre del archivo de la plantilla.
- Un rechazo o un vencimiento de una aprobación hacen fallar a `Approval`. La ruta de fallo debe colgar de ella, no de la actividad siguiente; el test `test_rejected_or_expired_approval_goes_to_fail_not_to_notebook_b` lo protege.
