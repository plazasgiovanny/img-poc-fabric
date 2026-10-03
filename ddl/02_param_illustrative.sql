-- Parámetros ILUSTRATIVOS para que la demo corra. Reemplazar con los valores del manual vigente
-- cuando el equipo los entregue. Ninguno proviene del documento del caso ni del manual de la SDIS.

INSERT INTO param.targeting_criteria VALUES
 ('TARGETING_PLACEHOLDER_01', 'sisben_group', 'IN', 'A,B', DATE'2026-01-01', NULL, 'PENDING', 'PENDING (G3)', 1);

-- Reglas de bloqueo: marcas de la fuente de validación (la lógica de bloqueo real es PENDIENTE G4).
INSERT INTO param.block_rules VALUES
 ('BLOCK_PLACEHOLDER_01', 'Deceased person in the validation source', 'validation_status', '=', 'DECEASED',
  'DECEASED_IN_VALIDATION', DATE'2026-01-01', NULL, 'PENDING', 'PENDING (G4)', 1),
 ('BLOCK_PLACEHOLDER_02', 'Person not found in the validation source', 'validation_found', '=', 'NO',
  'NOT_FOUND_IN_VALIDATION', DATE'2026-01-01', NULL, 'PENDING', 'PENDING (G4)', 1);

INSERT INTO param.holder_rule VALUES
 (1, 'birth_date', 'ASC', DATE'2026-01-01', NULL, 'PENDING', 'PENDING (G5)', 1),
 (2, 'doc_number', 'ASC', DATE'2026-01-01', NULL, 'PENDING', 'PENDING (G5)', 1);

INSERT INTO param.operators VALUES
 ('OPERATOR_A', 1, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('OPERATOR_B', 2, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1);

INSERT INTO param.amounts VALUES
 ('BASE_HOUSEHOLD_AMOUNT', 100000.0, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1);

INSERT INTO param.funding_sources VALUES
 ('SOURCE_X', 50000000.0, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1);

INSERT INTO param.payment_list_partition VALUES
 ('operator,funding_source', DATE'2026-01-01', NULL, 'PENDING', 'PENDING (G7)', 1);
