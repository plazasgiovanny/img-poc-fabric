# Pipeline `pl_img_cycle`

> Inventario de pipelines, plantillas JSON sin IDs y la herramienta para generarlos: [`INVENTORY.md`](INVENTORY.md).

El pipeline se versionará aquí como JSON (`pl_img_cycle.json`); la intención es generarlo con `scripts/pipeline_tool.py` a partir de una plantilla (ver [`INVENTORY.md`](INVENTORY.md)). **`pl_img_cycle` todavía no existe**: esta guía fija la estructura que debe tener (§18.3 y §19).

**Parámetros del pipeline:** `cycle_id`, `cutoff` (`cutoff1` o `cutoff2`), `cutoff_date`. Usar un `cycle_id`
nuevo por corrida (p. ej. `2026-09-r1`): repetirlo duplica filas.

| # | Actividad | Tipo | Parámetros | Si falla |
|---|---|---|---|---|
| 1 | `init` | Notebook `nb_init_cycle` | `cycle_id`, `cutoff`, `cutoff_date` | Falla el pipeline |
| 2 | `orch_e1` | Notebook `nb_orch_e1` | `cycle_id` | Falla el pipeline |
| 3 | `ctl_c1_summary` | Notebook `nb_ctl_summary` | `cycle_id`, `control=C1` | Falla el pipeline |
| 4 | `approval_c1` | **Approval** (`ApprovalGroupChatMessage`, chat de Teams) o Plan B | `approvers`, título y descripción con el resumen de 3; timeout = plazo (G8, mínimo 10 min) | La flecha **Failed** sale de esta actividad hacia 5r |
| 5 | `record_c1` | Notebook `nb_record_approval` | `control=C1`, `decision=APPROVED`, `approver`, `mechanism=approval_activity` | Falla |
| 5r | `reject_c1` | Notebook `nb_record_approval` | `control=C1`, `decision=REJECTED`, o `EXPIRED` si el error es `ActionTimedOut`; luego una actividad **Fail** con el mensaje del error | — |
| 6–9 | `orch_e2` + C2 | igual que 2–5 con `nb_orch_e2`, `control=C2` | | |
| 10–13 | `orch_settlement` + C3 | igual con `nb_orch_settlement`, `control=C3` | | |
| 14 | `orch_payment_lists` | Notebook `nb_orch_payment_lists` | `cycle_id` | Falla |
| 15–18 | C4 | `nb_ctl_summary` (`control=C4`) → aprobación → registrar | | |
| 19 | `publish` | Notebook `nb_07_publish` | `cycle_id` | Falla (no publica si falta un control aprobado) |
| 20 | ~~`report_final`~~ | **No se genera** | | `nb_06_report` ya corre dentro de `nb_orch_payment_lists` (`DAG_PAYMENT_LISTS` en `img_lib/dag.py`); repetirlo duplicaría el informe. Desviación respecto al diseño original. |

La plantilla generada (`templates/pl_img_cycle.template.json`) tiene 26 actividades: las 20 de arriba menos `report_final`, más una actividad `Fail` por control (`fail_c1`..`fail_c4`) tras cada `reject_cX`. Orden: `init` → `orch_e1` → C1 → `orch_e2` → C2 → `orch_settlement` → C3 → `orch_payment_lists` → C4 → `publish`, donde cada control es `ctl_cX_summary` → `approval_cX` → `record_cX` (y `approval_cX` Failed → `reject_cX` → `fail_cX`). Timeout de cada Approval: 30 min. No se pasa `NOTEBOOK_VERSION` desde el pipeline.

**Mecanismo de aprobación (verificado con `pl_env_check_approval`, G10 cerrado)**
- **Plan A:** actividad *Approval*, que está en **vista previa** (el nodo se titula «Aprobación (vista previa)»; Microsoft
  puede cambiar su comportamiento o su JSON).
  - **Cómo funciona:** su tipo es `ApprovalGroupChatMessage`. Publica un aviso en un chat de Teams
    (`[APPROVAL REQUIRED] … Approver: <correo> … View request on Fabric`) sin botones: la decisión se toma en Fabric,
    en el enlace «View request on Fabric». La actividad **espera** la decisión. No confundir con la actividad *Teams*, que solo publica un mensaje y no espera.
  - **Qué devuelve:** si se aprueba, la salida es solo `{"message": "Your request is approved. "}`. **No trae aprobador ni hora.**
  - **Cómo se distinguen los tres desenlaces:**

    | Desenlace | Estado de `Approval1` | Se reconoce por |
    |---|---|---|
    | Aprobado | Éxito; sigue la actividad siguiente | Salida con `Your request is approved.` |
    | Rechazado | Falla | Mensaje `Your request is rejected. … Status code from callback: BadRequest` |
    | Vencido | Falla | Código `ActionTimedOut`, mensaje `Activity timed out` |

    El timeout mínimo que acepta el portal es de 10 minutos.
  - **Ruta de fallo:** la flecha *Failed* debe salir de `Approval1`, no de la actividad siguiente (esa nunca se ejecuta).
    La actividad `Fail` puede mostrar el motivo con el mensaje dinámico `@activity('Approval1').error.message`
    (verificado). Si una actividad recibe varias flechas de entrada, se combinan con «y» (comportamiento de Data Factory; **no verificado en Fabric**).
  - **Qué se registra en `ctl.approvals`:** `approver` = el valor de `approvers` configurado; `decided_at` = `utcNow()` al
    terminar la actividad; `mechanism = approval_activity`; `decision` según la tabla anterior.
  - **Premisa no verificada:** el equipo asume que solo el usuario designado puede aprobar; no se probó que otro miembro
    del chat no pueda. El documento (§23) debe declarar esta limitación y que la actividad está en vista previa.
  - **`nb_record_approval` y `decided_at`:** cerrado: el cuaderno recibe `decided_at` (el pipeline pasa `@utcNow()`); si es `None` usa `now()`.
- **Plan B** (respaldo si la vista previa cambia o hace falta certeza sobre quién decide): después de `ctl_cX_summary`,
  `Until` con `Wait` de 60 s y `Lookup` sobre `ctl.approvals` hasta que exista una decisión distinta de `PENDING` para
  ese control; el timeout del `Until` es el plazo. El aprobador ejecuta `nb_approve`, que toma la identidad de la
  sesión. Si vence, se registra `EXPIRED`. *No verificado en Fabric.*

**Formato de parámetros de `TridentNotebook`** (tomado de un JSON exportado): en `typeProperties.parameters`,
`{"cycle_id": {"value": {"value": "@pipeline().parameters.cycle_id", "type": "Expression"}, "type": "string"}}`; un literal va como `{"value": "C1", "type": "string"}`.

**No verificado sin Fabric:** la expresión de la descripción del Approval (`@concat(..., string(@activity('ctl_cX_summary').output.result.exitValue))`; si el portal no admite expresiones ahí, usar texto fijo), el literal de parámetros fijos, `@utcNow()` como valor de parámetro, `ActionTimedOut` dentro de `string(error)`, la combinación de flechas, y el comportamiento de `runMultiple` dentro de un pipeline.

## Obtener los IDs de cuaderno e importar `pl_img_cycle`
1. En un cuaderno de Fabric: `for n in notebookutils.notebook.list(): print(n.displayName, n.id)` (si el atributo falla, `print(n)` y ajusta el texto a líneas «nombre id»). Copia la salida a un archivo local (p. ej. `ids.txt`, no se versiona).
2. `python scripts/pipeline_tool.py ids-from-text ids.txt` (guarda en `pipelines/local.json`, ignorado por git; no imprime los IDs).
3. `python scripts/pipeline_tool.py render pl_img_cycle` (falla listando los cuadernos que falten) → `output/pipelines/pl_img_cycle.json`.
4. En Fabric crea un pipeline nuevo, abre el menú del lienzo, edita el JSON (pegar) y aplica. La importación sigue siendo manual ([issue #8](https://github.com/plazasgiovanny/img-poc-fabric/issues/8)).
5. Importa de nuevo `nb_record_approval` (nuevo parámetro `decided_at`).
