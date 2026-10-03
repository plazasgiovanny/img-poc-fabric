# Changelog

## [Sin publicar]
- Estructura inicial del repo, `img_lib` 0.1.0, generador sintético, DDL de control/parámetros,
  cuadernos de la Etapa 1 y CI.
- Etapas 2 y 3: cruces, liquidación mínima, controles, DAG, métricas, cuadernos y guía del pipeline.
- Verificación del entorno: `nb_env_check` (+2 hijos), `scripts/prepare_package.py` y `docs/ENV_CHECK.md`.
- Renombrado a inglés de archivos, módulos, funciones, variables, tablas, columnas y valores (ver `docs/NAMING.md`).
- `cycle.write` usa el esquema de la tabla existente y `run_log.record` lo reutiliza (columnas con None); `nb_ctl_summary` tolera la ausencia de la tabla de cuarentena; nueva prueba en `nb_env_check`.
- Inventario de pipelines (`pipelines/INVENTORY.md`), plantilla de `pl_env_check_approval` sin IDs y `scripts/pipeline_tool.py` (render / templatize).
- G10 cerrado: resultados de las tres corridas de la aprobación y criterio para registrar al aprobador (`pipelines/INVENTORY.md`).
