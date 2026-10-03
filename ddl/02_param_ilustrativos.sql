-- Parámetros ILUSTRATIVOS para que la demo corra. Reemplazar con los valores del manual vigente
-- cuando el equipo los entregue. Ninguno proviene del documento del caso ni del manual de la SDIS.

INSERT INTO param.criterios_focalizacion VALUES
 ('FOC_PLACEHOLDER_01', 'grupo_sisben', 'IN', 'A,B', DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE (G3)', 1);

-- Reglas de bloqueo: marcas de la fuente de validación (la lógica de bloqueo real es PENDIENTE G4).
INSERT INTO param.reglas_bloqueo VALUES
 ('BLQ_PLACEHOLDER_01', 'Persona fallecida en la fuente de validación', 'estado_validacion', '=', 'FALLECIDO',
  'FALLECIDO_EN_VALIDACION', DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE (G4)', 1),
 ('BLQ_PLACEHOLDER_02', 'Persona no encontrada en la fuente de validación', 'encontrado_validacion', '=', 'NO',
  'NO_ENCONTRADO_EN_VALIDACION', DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE (G4)', 1);

INSERT INTO param.regla_titular VALUES
 (1, 'fecha_nacimiento', 'ASC', DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE (G5)', 1),
 (2, 'num_doc', 'ASC', DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE (G5)', 1);

INSERT INTO param.operadores VALUES
 ('OPERADOR_A', 1, DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE', 1),
 ('OPERADOR_B', 2, DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE', 1);

INSERT INTO param.montos VALUES
 ('MONTO_BASE_HOGAR', 100000.0, DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE', 1);

INSERT INTO param.fuentes_recursos VALUES
 ('FUENTE_X', 50000000.0, DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE', 1);

INSERT INTO param.particion_listados VALUES
 ('operador,fuente_recursos', DATE'2026-01-01', NULL, 'PENDIENTE', 'PENDIENTE (G7)', 1);
