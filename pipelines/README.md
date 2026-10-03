# Pipeline `pl_img_ciclo`

El pipeline se arma en el portal de Fabric (Data Factory) y se exporta aquí como JSON
(`pl_img_ciclo.json`) cuando esté probado. Esta guía fija la estructura que debe tener (§18.3 y §19).

**Parámetros del pipeline:** `id_ciclo`, `corte` (`corte1` o `corte2`), `fecha_corte`. Usar un `id_ciclo`
nuevo por corrida (p. ej. `2026-09-r1`): repetirlo duplica filas.

| # | Actividad | Tipo | Parámetros | Si falla |
|---|---|---|---|---|
| 1 | `ini` | Notebook `nb_ini_ciclo` | `id_ciclo`, `corte`, `fecha_corte` | Falla el pipeline |
| 2 | `orq_e1` | Notebook `nb_orq_e1` | `id_ciclo` | Falla el pipeline |
| 3 | `ctl_c1_resumen` | Notebook `nb_ctl_resumen` | `id_ciclo`, `control=C1` | Falla el pipeline |
| 4 | `aprobacion_c1` | **Approval** (Outlook o Teams) o Plan B | mensaje = `exitValue` de 3; timeout = plazo (G8) | Ruta de rechazo → 5r |
| 5 | `registrar_c1` | Notebook `nb_registrar_aprobacion` | `control=C1`, `decision=APROBADO` | Falla |
| 5r | `rechazar_c1` | Notebook `nb_registrar_aprobacion` | `control=C1`, `decision=RECHAZADO` (o `VENCIDO` si fue timeout) → actividad **Fail** | — |
| 6–9 | `orq_e2` + C2 | igual que 2–5 con `nb_orq_e2`, `control=C2` | | |
| 10–13 | `orq_liq` + C3 | igual con `nb_orq_liq`, `control=C3` | | |
| 14 | `orq_listados` | Notebook `nb_orq_listados` | `id_ciclo` | Falla |
| 15–18 | C4 | `nb_ctl_resumen` (`control=C4`) → aprobación → registrar | | |
| 19 | `publicar` | Notebook `nb_07_publicar` | `id_ciclo` | Falla (no publica si falta un control aprobado) |
| 20 | `informe_final` | Notebook `nb_06_informe` | `id_ciclo` | Falla |

**Mecanismo de aprobación**
- **Plan A:** actividad *Approval* (Outlook 365 o Teams). Se decide en Monitoring Hub > Review. Si vence el
  timeout, la actividad falla y sigue la ruta de rechazo (§19). No aplica control de acceso por rol: el
  aprobador queda registrado en `ctl.aprobaciones` y se contrasta con el rol esperado de la Tabla 9.
- **Plan B** (tenant sin buzón de Microsoft 365): después de `ctl_cX_resumen`, `Until` con `Wait` de 60 s y
  `Lookup` sobre `ctl.aprobaciones` hasta que exista una decisión distinta de `PENDIENTE` para ese control;
  el timeout del `Until` es el plazo. El aprobador ejecuta `nb_aprobar`. Si vence, se registra `VENCIDO`.

**Verificar en el spike del día 1** (G10): si la salida de la actividad *Approval* trae aprobador y hora; si no,
tomarlos de Monitoring Hub > Review.
