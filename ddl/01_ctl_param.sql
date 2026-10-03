-- Esquemas de control y parámetros (lakehouse lh_control, Spark SQL / Delta).
-- Los parámetros de ejemplo van con is_illustrative = 1: NO son reglas del manual de la SDIS
-- hasta que el equipo los confirme (PENDIENTES G3-G7).

CREATE SCHEMA IF NOT EXISTS ctl;
CREATE SCHEMA IF NOT EXISTS param;

CREATE TABLE IF NOT EXISTS ctl.cycle (
  cycle_id STRING, cutoff STRING, cutoff_date DATE, population_source_version STRING, validation_source_version STRING,
  created_at STRING
) USING DELTA;

-- Instrumento A (Tabla 2, 11 campos + observaciones) + trazabilidad (Tabla 7)
CREATE TABLE IF NOT EXISTS ctl.run_log (
  batch_id STRING, cycle_date STRING, start_time STRING, end_time STRING,
  records_processed BIGINT, manual_labor_hours DOUBLE, duplicate_errors BIGINT,
  process_stage STRING, processing_mode STRING, trace_event STRING, data_source STRING,
  notes STRING,
  cycle_id STRING, execution_id STRING, pipeline_run_id STRING, notebook STRING, notebook_version STRING,
  version_lib STRING, user_name STRING, target_table STRING, delta_target_version BIGINT, output_hash STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS ctl.approvals (
  cycle_id STRING, control STRING, responsible_role STRING, requested_at STRING, decided_at STRING,
  decision STRING, approver STRING, comment STRING, mechanism STRING, pipeline_run_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS ctl.exp_metrics (
  cycle_id STRING, execution_id STRING, metric STRING, value DOUBLE, detail STRING, measured_at STRING
) USING DELTA;

-- Parámetros de la Etapa 3 (§18): vigencia, responsable y documento soporte en cada fila.
CREATE TABLE IF NOT EXISTS param.targeting_criteria (
  criterion STRING, field STRING, operator STRING, value STRING,
  valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.block_rules (
  rule_id STRING, description STRING, field STRING, operator STRING, value STRING, reason STRING,
  valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.holder_rule (
  rank INT, criterion STRING, sort_direction STRING,
  valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.operators (
  operator STRING, priority INT,
  valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.amounts (
  concept STRING, amount DOUBLE,
  valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.funding_sources (
  funding_source STRING, ceiling DOUBLE,
  valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.payment_list_partition (
  split_by STRING, valid_from DATE, valid_to DATE, owner STRING, support_document STRING, is_illustrative INT
) USING DELTA;
