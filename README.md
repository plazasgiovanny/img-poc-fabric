# PoC IMG en Microsoft Fabric (trial)

Mini demo de la arquitectura del caso de análisis *Automatización de la integración de datos del programa
Ingreso Mínimo Garantizado (IMG), SDIS Bogotá* (documento `Caso_Analisis_IMG_Automatizacion_v2`, §16–§19).

**Alcance:** una fuente poblacional + una fuente de validación (no las 13), recorriendo Bronce → Plata (+MDM)
→ Oro → base de cruces → liquidación mínima → 4 controles humanos → listado + informe.

> **Datos 100 % sintéticos.** Este repositorio es público: nunca se versionan datos, credenciales, IDs de
> tenant ni correos (Ley 1581 de 2012). Los datos se regeneran con la semilla (`generador/`).
> Todo parámetro de negocio marcado `es_ilustrativo = 1` **no** proviene del manual de la SDIS; ver
> [`docs/PENDIENTES.md`](docs/PENDIENTES.md).

## Estructura
| Carpeta | Contenido |
|---|---|
| `img_lib/` | Biblioteca común (`.whl` para el Environment `env_img`): normalización, MDM, bitácora, parámetros vigentes, huella SHA-256 |
| `notebooks/` | Cuadernos de Fabric exportados como `.py` (celdas `# %%`) |
| `ddl/` | Esquemas `ctl.*` y `param.*` y parámetros ilustrativos |
| `generador/` | Generador determinista de datos sintéticos con defectos inyectados y verdad conocida |
| `pipelines/` | JSON exportado de `pl_img_ciclo` (cuando exista) |
| `tests/` | pytest de la lógica pura (normalización, MDM contra la verdad, bitácora, generador) |
| `docs/` | Pendientes, decisiones y evidencias |

## Estado
| Componente | Estado |
|---|---|
| `img_lib` (normalizar, validar, params, huella, bitácora, MDM, cruces, liquidación, controles, DAG, métricas) | Hecho, con pruebas locales |
| Cadena lógica completa sobre datos sintéticos (`tests/test_e2e.py`) | Hecho: error <1 % a 500 y a 5.000 registros |
| Generador sintético | Hecho (esquema **provisional**, PENDIENTE G2) |
| DDL `ctl/param` + parámetros ilustrativos | Hecho |
| Cuadernos (Etapas 1 a 3, controles, orquestadores `runMultiple`) | Escritos y con sintaxis verificada, **sin ejecutar en Fabric** (spike día 1) |
| Pipeline `pl_img_ciclo` con 4 aprobaciones | Guía en `pipelines/README.md`; se arma en el portal y se exporta |

Desviaciones deliberadas respecto del documento (ver `docs/PENDIENTES.md`): un solo workspace con 4 lakehouses,
un cuaderno de Plata para ambas fuentes (la PoC tiene dos), publicación en OneLake en vez de Azure Storage.

## Desarrollo local
```bash
pip install pytest ruff build
pytest -q tests
ruff check .
python -m build --wheel img_lib          # genera img_lib/dist/img_lib-*.whl
python generador/generador.py --n 500 --corte 1 --salida data   # data/ está en .gitignore
```

## Despliegue en el trial de Fabric (resumen)
1. Crear workspace `IMG_PoC` y 4 lakehouses con schemas: `lh_bronce`, `lh_plata`, `lh_oro`, `lh_control`
   (`lh_control` = lakehouse por defecto de **todos** los cuadernos).
2. Crear el Environment `env_img`, subir el `.whl` (modo Quick) y publicarlo.
3. Ejecutar `ddl/01_ctl_param.sql` y `ddl/02_param_ilustrativos.sql` en `lh_control`; crear los schemas
   `bronce`, `calidad`, `poblacional`, `validacion`, `mdm`, `fuentes`, `cruces`, `liquidacion` en su lakehouse.
4. Subir a `lh_control/Files/sinteticos/landing/corte1/` los CSV del generador (`poblacional.csv`,
   `validacion.csv`); `verdad/` queda fuera del pipeline.
5. Importar los `.py` de `notebooks/` y ejecutar en orden. `VERSION_CUADERNO` se reemplaza por el SHA/tag.

## Flujo de trabajo con Git
- `main` protegida = lo que se importa al workspace. Trabajo en `feature/<rol>-<tema>`, PR revisado por otra
  persona, CI en verde, squash merge. Commits en español con prefijo (`feat:`, `fix:`, `docs:`, `test:`).
- Tags de hito: `v0.1-etapa1`, `v0.2-e2e`, `v1.0-demo` (el release adjunta el `.whl` y el JSON del pipeline).
- Al cambiar el pipeline en el portal, exportar el JSON a `pipelines/` y commitear.
