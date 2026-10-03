-- Esquemas de control y parámetros (lakehouse lh_control, Spark SQL / Delta).
-- Los parámetros de ejemplo van con es_ilustrativo = 1: NO son reglas del manual de la SDIS
-- hasta que el equipo los confirme (PENDIENTES G3-G7).

CREATE SCHEMA IF NOT EXISTS ctl;
CREATE SCHEMA IF NOT EXISTS param;

CREATE TABLE IF NOT EXISTS ctl.ciclo (
  id_ciclo STRING, corte STRING, fecha_corte DATE, version_fuente_poblacional STRING, version_fuente_validacion STRING,
  creado_en STRING
) USING DELTA;

-- Instrumento A (Tabla 2, 11 campos + observaciones) + trazabilidad (Tabla 7)
CREATE TABLE IF NOT EXISTS ctl.bitacora_ejecucion (
  id_lote STRING, fecha_ciclo STRING, hora_inicio STRING, hora_fin STRING,
  num_registros_procesados BIGINT, horas_hombre_manual DOUBLE, num_errores_duplicidad BIGINT,
  etapa_proceso STRING, modo_procesamiento STRING, evento_trazabilidad STRING, fuente_dato STRING,
  observaciones STRING,
  id_ciclo STRING, id_ejecucion STRING, pipeline_run_id STRING, cuaderno STRING, version_cuaderno STRING,
  version_lib STRING, usuario STRING, tabla_destino STRING, version_delta_destino BIGINT, hash_salida STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS ctl.aprobaciones (
  id_ciclo STRING, control STRING, rol_responsable STRING, solicitado_en STRING, decidido_en STRING,
  decision STRING, aprobador STRING, comentario STRING, mecanismo STRING, pipeline_run_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS ctl.metricas_exp (
  id_ciclo STRING, id_ejecucion STRING, metrica STRING, valor DOUBLE, detalle STRING, medido_en STRING
) USING DELTA;

-- Parámetros de la Etapa 3 (§18): vigencia, responsable y documento soporte en cada fila.
CREATE TABLE IF NOT EXISTS param.criterios_focalizacion (
  criterio STRING, campo STRING, operador STRING, valor STRING,
  vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.reglas_bloqueo (
  id_regla STRING, descripcion STRING, campo STRING, operador STRING, valor STRING, causal STRING,
  vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.regla_titular (
  orden INT, criterio STRING, direccion STRING,
  vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.operadores (
  operador STRING, prioridad INT,
  vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.montos (
  concepto STRING, monto DOUBLE,
  vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.fuentes_recursos (
  fuente_recursos STRING, techo DOUBLE,
  vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
CREATE TABLE IF NOT EXISTS param.particion_listados (
  por STRING, vigente_desde DATE, vigente_hasta DATE, responsable STRING, documento_soporte STRING, es_ilustrativo INT
) USING DELTA;
