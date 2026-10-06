# PoC IMG en Microsoft Fabric (trial)

Mini demo de la arquitectura del caso de análisis *Automatización de la integración de datos del programa
Ingreso Mínimo Garantizado (IMG), SDIS Bogotá* (documento `Caso_Analisis_IMG_Automatizacion_v2`, §16–§19).

**Alcance:** simulación funcional a escala básica (500 registros, extrapolable a 10x: la cadena también corre a 5.000) con la base maestra
poblacional y la base de inhumados, recorriendo Bronce → Plata (+MDM) → Oro → base de cruces → liquidación → 4 controles humanos →
listados `.xlsx` por operador + informe.

**Qué demuestra frente al proceso manual:** trazabilidad por ciclo (`ctl.run_log`, `execution_id` en cada commit Delta y huella SHA-256 de
las entregas y los listados), reglas como datos (`param.*` con vigencia, no código), cuatro controles con aprobación humana,
reproducibilidad (misma semilla, mismos datos) y menos pasos manuales entre la fuente y el listado de dispersión.

> **Datos 100 % sintéticos.** Este repositorio es público: nunca se versionan datos, credenciales, IDs de
> tenant ni correos (Ley 1581 de 2012). Los datos se regeneran con la semilla (`generator/`).
> Todo parámetro de negocio marcado `is_illustrative = 1` **no** proviene del manual de la SDIS; ver
> [`docs/OPEN_ITEMS.md`](docs/OPEN_ITEMS.md).

## Estructura
| Carpeta | Contenido |
|---|---|
| `img_lib/` | Biblioteca común (`.whl` para el Environment `env_img`): normalización, MDM, bitácora, parámetros vigentes, huella SHA-256 |
| `notebooks/` | 26 cuadernos de Fabric como `.py` (celdas `# %%`; el paquete los convierte a `.ipynb`): 23 de la cadena y 3 de verificación del entorno |
| `ddl/` | Esquemas `ctl.*` y `param.*` y parámetros ilustrativos (Spark SQL) |
| `generator/` | Generador determinista de datos sintéticos con defectos inyectados y verdad conocida |
| `scripts/` | `prepare_package.py` (arma el paquete para subir a Fabric) y `pipeline_tool.py` (genera pipelines desde plantillas) |
| `pipelines/` | [Inventario](pipelines/INVENTORY.md), plantillas JSON sin IDs y [guía de `pl_img_cycle`](pipelines/README.md) |
| `tests/` | pytest de la lógica pura (normalización, MDM contra la verdad, bitácora, generador, plantillas de pipelines) |
| `docs/` | [Pendientes](docs/OPEN_ITEMS.md), [decisiones de diseño](docs/DESIGN_DECISIONS.md), [verificación del entorno](docs/ENV_CHECK.md), [nombres](docs/NAMING.md), [historial](docs/timeline.html) |

## Estado
| Componente | Estado |
|---|---|
| `img_lib` (`mapping`, `dispersal`, `normalize`, `validate`, `params`, `fingerprint`, `run_log`, `mdm`, `crosschecks`, `settlement`, `controls`, `dag`, `metrics`, `cycle`) | Hecho, con pruebas locales; `img_lib` se importa desde el Environment en Fabric |
| Cadena lógica completa sobre datos sintéticos (`tests/test_e2e.py`) | Hecho, en local: error <1 % a 500 y a 5.000 registros |
| Generador sintético | Hecho, con el esquema real (`RSH_*`/`SIS_*`, separador `||`) y la base de inhumados |
| DDL `ctl/param` + parámetros ilustrativos | **Aplicado en Fabric** (`lh_control`) |
| Entorno (workspace `IMG_PoC`, 4 lakehouses, Environment `env_img`) | **Verificado**: `nb_env_check` 13 de 13 OK ([resultado](docs/ENV_CHECK.md)) |
| Cuadernos `nb_env_check*` (3) | Escritos y **ejecutados en Fabric** |
| Los otros 23 cuadernos (Etapas 1 a 3, controles, orquestadores) | Escritos y con sintaxis verificada; **aún no importados ni ejecutados en Fabric** |
| Aprobación humana (G10) | **Verificada** con `pl_env_check_approval` (aprobada, rechazada y vencida); la actividad está en vista previa |
| Pipeline `pl_img_cycle` con 4 aprobaciones | Planeado; guía en [`pipelines/README.md`](pipelines/README.md), falta generarlo |
| Capa de mapeo de nombres reales a internos (`img_lib.mapping`) y listados `.xlsx` (`img_lib.dispersal`) | Hecho, con pruebas locales; ver [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) |

Desviaciones deliberadas respecto del documento (ver `docs/OPEN_ITEMS.md`): un solo workspace con 4 lakehouses,
un cuaderno de Plata para ambas fuentes (la PoC tiene dos), publicación en OneLake en vez de Azure Storage.

## Qué falta
1. Correr en Fabric la cadena con el esquema real: volver a subir datos y wheel, reaplicar el DDL de parámetros (ver `docs/ENV_CHECK.md`).
2. Importar los 23 cuadernos a Fabric (lakehouse por defecto, Environment y celda de parámetros en cada uno).
3. Generar `pl_img_cycle`; falta saber cómo espera Fabric los parámetros de la actividad de cuaderno.
4. Tres corridas medidas de 500 registros (Experimento 2) y, opcional, una de 5.000.
5. Línea base manual (G1) para medir la reducción de tiempo ≥30 %.

Detalle y responsables: [`docs/OPEN_ITEMS.md`](docs/OPEN_ITEMS.md). Historial: [`docs/timeline.html`](docs/timeline.html).

## Desarrollo local
```bash
pip install pytest ruff build openpyxl
pytest -q tests
ruff check .
python -m build --wheel img_lib          # genera img_lib/dist/img_lib-*.whl
python generator/generator.py --n 500 --cutoff 1 --output data   # data/ está en .gitignore
```

## Despliegue en el trial de Fabric (resumen)
La guía completa, con los errores que aparecieron, está en [`docs/ENV_CHECK.md`](docs/ENV_CHECK.md). El paquete para
subir se arma con `python scripts/prepare_package.py` (genera `output/fabric_package/`, ignorado por git).

1. Crear workspace `IMG_PoC` y 4 lakehouses con schemas: `lh_bronze`, `lh_silver`, `lh_gold`, `lh_control`
   (`lh_control` = lakehouse por defecto de **todos** los cuadernos).
2. Crear el Environment `env_img`, subir el `.whl` (modo Quick), **publicarlo** y **adjuntarlo** a cada cuaderno
   (o fijarlo como predeterminado del workspace); reiniciar la sesión.
3. Aplicar `ddl/01_ctl_param.sql` y `ddl/02_param_illustrative.sql` **desde un cuaderno** con `lh_control` por
   defecto (Spark SQL, una sentencia por llamada; no sirve el SQL analytics endpoint). Los demás esquemas
   (`bronze`, `quality`, `population`, `validation`, `mdm`, `sources`, `crosschecks`, `settlement`) los crea `nb_env_check`.
4. Subir a `lh_control/Files/synthetic/landing/cutoff1/` los CSV del generador (`population.csv` = base maestra y
   `validation.csv` = inhumados, ambos separados por `||`); `ground_truth/` queda fuera del pipeline.
5. Importar `nb_env_check` y sus dos hijos, y ejecutar `nb_env_check` (esperado: 13 OK).
6. Importar los demás cuadernos de `notebooks/` (aún pendiente) y ejecutarlos en el orden de los orquestadores.
   `NOTEBOOK_VERSION` se reemplaza por el SHA/tag al preparar el paquete.

## Flujo de trabajo con Git
- `main` protegida = lo que se importa al workspace. Trabajo en `feature/*`, `fix/*` o `docs/*`, PR a `main`,
  CI (ruff, pytest y build del wheel) en verde y merge con commit de merge. Commits en español con prefijo (`feat:`, `fix:`, `docs:`, `refactor:`).
- Tags de hito previstos (aún no creados): `v0.1-etapa1`, `v0.2-e2e`, `v1.0-demo` (el release adjunta el `.whl` y el JSON del pipeline).
- Al cambiar el pipeline en el portal, traer el JSON con `scripts/pipeline_tool.py templatize` (ver `pipelines/INVENTORY.md`) y commitear la plantilla.
