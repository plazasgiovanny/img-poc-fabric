# Pendientes y supuestos (no se asumen)

Nada de lo siguiente está definido en el documento v2 ni lo ha confirmado el equipo. Mientras tanto la PoC usa
un placeholder parametrizado con `es_ilustrativo = 1`, visible en el informe de generación.

| ID | Pendiente | Placeholder actual | Quién lo resuelve |
|---|---|---|---|
| G1 | Línea base manual para el criterio de reducción ≥30 % (¿medirla sobre los mismos 500 registros?) | Columna "manual" de la Tabla 4 sin llenar | Equipo |
| G2 | Las dos fuentes concretas y su diccionario de datos (campos, tipos, formato, separador, codificación) | `poblacional` / `validacion`, esquema provisional en `generador/` | Compañero |
| G3 | Criterios de focalización | `FOC_PLACEHOLDER_01` | Compañero (manual SDIS) |
| G4 | Reglas de bloqueo (el doc menciona 15, no las enumera) | `BLQ_PLACEHOLDER_01/02` | Compañero |
| G5 | Regla de selección de titular | Orden ilustrativo en `param.regla_titular` | Compañero |
| G6 | Umbrales y reglas de coincidencia/supervivencia del MDM | Documento exacto; prevalece la fuente poblacional (`img_lib.mdm`) | Equipo |
| G7 | Estructura del listado por operador | Columnas de la Tabla 7 | Compañero |
| G8 | Plazo y canal de cada control | 30 min en la demo | Equipo |
| G9 | Orden de dependencias entre cuadernos (el §23 lo marca como supuesto) | El de la Tabla 8 | Equipo |
| G10 | ¿El output de la Approval activity incluye aprobador y hora? | Se verifica en el spike del día 1 | Plataforma |
| G11 | Costo operativo por ciclo (Tabla 4) | CU·s × precio de lista, declarado como estimado | Equipo |
