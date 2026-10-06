-- Parámetros de la Etapa 3 para la demo. Espejo de img_lib/illustrative.py.
-- Focalización, bloqueos y criterios del titular son los definidos por el equipo de la fuente (is_illustrative = 0);
-- is_illustrative = 1 queda solo en los valores de demostración (operadores habilitados, fuente de financiación, partición).
-- El script es repetible: vacía cada tabla antes de insertar (no hay que borrar las tablas al cambiar de versión).

DELETE FROM param.targeting_criteria;
INSERT INTO param.targeting_criteria VALUES
 ('SISBEN_GROUP_A', 'sisben_group', '=', '1. SISBEN IV - A', DATE'2026-01-01', NULL, 'SDIS', 'RSH_grupo_S4 = ''1. SISBEN IV - A''', 0);

-- Bloqueos: vigencia RENEC fuera de (0,12) (nula no bloquea) y existencia en la base de inhumados (tipo + número).
DELETE FROM param.block_rules;
INSERT INTO param.block_rules VALUES
 ('BLOCK_RENEC', 'RENEC validity not in (0,12)', 'renec_validity', 'NOT IN', '0,12',
  'RENEC_NOT_VALID', DATE'2026-01-01', NULL, 'SDIS', 'RSH_vigencia_renec NOT IN (0,12)', 0),
 ('BLOCK_DECEASED_REGISTRY', 'Person exists in the deceased registry (document type + number)', 'validation_found', '=', 'YES',
  'IN_DECEASED_REGISTRY', DATE'2026-01-01', NULL, 'SDIS', 'Base de inhumados', 0);

-- Titular del hogar. sort_direction: ASC/DESC ordenan; REQUIRED filtra (el criterio debe cumplirse).
DELETE FROM param.holder_rule;
INSERT INTO param.holder_rule VALUES
 (1, 'is_adult', 'REQUIRED', DATE'2026-01-01', NULL, 'SDIS', 'Titular: mayor de edad', 0),
 (2, 'is_eligible', 'REQUIRED', DATE'2026-01-01', NULL, 'SDIS', 'Titular entre elegibles: adulta, focalizada y no bloqueada', 0),
 (3, 'is_woman', 'DESC', DATE'2026-01-01', NULL, 'SDIS', 'Titular: prioridad a la mujer del hogar', 0),
 (4, 'is_banked', 'DESC', DATE'2026-01-01', NULL, 'SDIS', 'Titular: bancarizada', 0),
 (5, 'age', 'DESC', DATE'2026-01-01', NULL, 'SDIS', 'Desempate: mayor edad', 0),
 (6, 'doc_number', 'ASC', DATE'2026-01-01', NULL, 'SDIS', 'Desempate: número de documento ascendente', 0);

-- Operadores de la maestra (Cuenta1); el de prioridad 1 es el de respaldo cuando la titular no tiene operador.
DELETE FROM param.operators;
INSERT INTO param.operators VALUES
 ('EFECTY', 1, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('DAVIPLATA', 2, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('NEQUI', 3, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('ALM', 4, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('MOVII', 5, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('DALE', 6, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1),
 ('POWWI', 7, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1);

DELETE FROM param.amounts;
INSERT INTO param.amounts VALUES
 ('BASE_HOUSEHOLD_AMOUNT', 120000.0, DATE'2026-01-01', NULL, 'SDIS', 'Diccionario de listados de dispersión (sdp_monto)', 0);

DELETE FROM param.funding_sources;
INSERT INTO param.funding_sources VALUES
 ('SOURCE_X', 100000000.0, DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1);

DELETE FROM param.payment_list_partition;
INSERT INTO param.payment_list_partition VALUES
 ('operator', DATE'2026-01-01', NULL, 'PENDING', 'PENDING', 1);
