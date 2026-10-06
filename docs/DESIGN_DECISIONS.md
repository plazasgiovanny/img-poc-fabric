# Decisiones de diseño y alcance de la PoC

Esquema de datos: base maestra poblacional (en producción, vista de SQL Server; en la PoC, CSV `||`, UTF-8, fechas ISO, sin comillas,
con encabezado) y base de inhumados para validar. Diccionarios: *Variables Base Maestra procesada* y *Listados de dispersión*.
Las reglas de focalización, bloqueo y titular vienen del equipo de la fuente; lo siguiente es el detalle fino que el código fija.

| # | Decisión | Dónde |
|---|---|---|
| D1 | Identidad de una persona = tipo + número de documento. «Existe en inhumados» = hay una fila con el mismo tipo y número (mismo número con otro tipo no cruza). | `mdm.match_key`, regla `BLOCK_DECEASED_REGISTRY` |
| D2 | Vigencia RENEC nula o ausente no bloquea; 0 y 12 son vigentes; cualquier otro código bloquea (operador `NOT IN`, nulo no cumple). | `settlement._matches`, `BLOCK_RENEC` |
| D3 | Titular del hogar: mayor de edad (>= 18) y no bloqueada (obligatorios); luego mujer (`RSH_sexo_persona` = 2), luego bancarizada (`SIS_bancarizado` = 1) como preferencia, no descarte; desempate por mayor edad y número de documento ascendente. | `param.holder_rule`, `settlement.select_holder` |
| D4 | La focalización es por persona (`RSH_grupo_S4 = '1. SISBEN IV - A'`); un hogar sin integrante elegible adulto queda sin titular. | `param.targeting_criteria` |
| D5 | Tipo de documento: la maestra usa su catálogo (1 CC, 2 TI, 3 CE, 4 RC...) y el listado de dispersión otro (1 RC, 2 TI, 3 CC, 4 CE...); la equivalencia es una tabla explícita y probada. | `mapping.MASTER_TO_DISPERSAL_DOC_TYPE` |
| D6 | Listado: un `.xlsx` por operador, 32 columnas en orden, con los valores por defecto del diccionario (0, `SIN INFORMACION`, 999, `ZZ- SIN INFORMACION`); monto parametrizable en `param.amounts` (120000 por el diccionario). | `img_lib.dispersal` |
| D7 | `sdp_operador` es la entidad que dispersa (DAVIPLATA -> DAVIVIENDA, NEQUI -> BANCOLOMBIA, POWWI -> POWII) y `sdp_producto` el código `SIS_banca` de la cuenta. Si la titular no tiene operador, se asigna el de prioridad 1 de `param.operators`. | `mapping.ACCOUNT_OPERATORS`, `assign_payment_method` |
| D8 | Identificadores del listado generados de forma determinista desde `cycle_id` y el número de fila: `sdp_id_listado` = `1` + ciclo + fila (6 dígitos), `sdp_id_IMG` = `2` + ciclo + fila, `sdp_id_pago` = `IMG-<ciclo>-<fila>`, `sdp_Giro` = ciclo + `01`. Ciclo = dígitos de `cycle_id` (`2026-09` -> `202609`). | `dispersal.listing_ids` |
| D9 | No se aplica bloqueo por edad: los menores no se descartan de la base, simplemente no pueden ser titulares. |  |
| D10 | Campos sin fuente en la PoC (UPZ, celular, cuenta, grupo/puntaje/clasificación SISBEN del listado, tipo de beneficiario, parqueadero) salen con el valor por defecto o vacíos del diccionario. | `dispersal.to_dispersal_row` |

Valores de demostración (`is_illustrative = 1`): operadores habilitados y su prioridad, fuente de financiación y techo, y partición de
los listados. Los datos son sintéticos (semilla fija) y no se versionan.
