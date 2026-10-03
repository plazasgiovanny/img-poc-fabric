# Pipeline `pl_img_cycle`

El pipeline se arma en el portal de Fabric (Data Factory) y se exporta aquí como JSON
(`pl_img_cycle.json`) cuando esté probado. Esta guía fija la estructura que debe tener (§18.3 y §19).

**Parámetros del pipeline:** `cycle_id`, `cutoff` (`cutoff1` o `cutoff2`), `cutoff_date`. Usar un `cycle_id`
nuevo por corrida (p. ej. `2026-09-r1`): repetirlo duplica filas.

| # | Actividad | Tipo | Parámetros | Si falla |
|---|---|---|---|---|
| 1 | `init` | Notebook `nb_init_cycle` | `cycle_id`, `cutoff`, `cutoff_date` | Falla el pipeline |
| 2 | `orch_e1` | Notebook `nb_orch_e1` | `cycle_id` | Falla el pipeline |
| 3 | `ctl_c1_summary` | Notebook `nb_ctl_summary` | `cycle_id`, `control=C1` | Falla el pipeline |
| 4 | `approval_c1` | **Approval** (Outlook o Teams) o Plan B | mensaje = `exitValue` de 3; timeout = plazo (G8) | Ruta de rechazo → 5r |
| 5 | `record_c1` | Notebook `nb_record_approval` | `control=C1`, `decision=APPROVED` | Falla |
| 5r | `reject_c1` | Notebook `nb_record_approval` | `control=C1`, `decision=REJECTED` (o `EXPIRED` si fue timeout) → actividad **Fail** | — |
| 6–9 | `orch_e2` + C2 | igual que 2–5 con `nb_orch_e2`, `control=C2` | | |
| 10–13 | `orch_settlement` + C3 | igual con `nb_orch_settlement`, `control=C3` | | |
| 14 | `orch_payment_lists` | Notebook `nb_orch_payment_lists` | `cycle_id` | Falla |
| 15–18 | C4 | `nb_ctl_summary` (`control=C4`) → aprobación → registrar | | |
| 19 | `publish` | Notebook `nb_07_publish` | `cycle_id` | Falla (no publica si falta un control aprobado) |
| 20 | `report_final` | Notebook `nb_06_report` | `cycle_id` | Falla |

**Mecanismo de aprobación**
- **Plan A:** actividad *Approval* (Outlook 365 o Teams). Se decide en Monitoring Hub > Review. Si vence el
  timeout, la actividad falla y sigue la ruta de rechazo (§19). No aplica control de acceso por rol: el
  aprobador queda registrado en `ctl.approvals` y se contrasta con el rol esperado de la Tabla 9.
- **Plan B** (tenant sin buzón de Microsoft 365): después de `ctl_cX_summary`, `Until` con `Wait` de 60 s y
  `Lookup` sobre `ctl.approvals` hasta que exista una decisión distinta de `PENDING` para ese control;
  el timeout del `Until` es el plazo. El aprobador ejecuta `nb_approve`. Si vence, se registra `EXPIRED`.

**Verificar con `nb_env_check`** (G10): si la salida de la actividad *Approval* trae aprobador y hora; si no,
tomarlos de Monitoring Hub > Review.
