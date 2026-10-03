"""Biblioteca común de la PoC IMG (§18: lectura de parámetros vigentes, validaciones,
bitácora de ejecución y escritura estandarizada). Sin dependencias duras: el núcleo es
Python puro; las funciones que tocan Spark/Delta importan `pyspark` de forma diferida."""

__version__ = "0.1.0"

from .huella import sha256_archivo, sha256_bytes  # noqa: F401
from .normalizar import (  # noqa: F401
    normalizar_documento,
    normalizar_fecha,
    normalizar_localidad,
    normalizar_nombre,
    normalizar_tipo_doc,
)
from .params import vigentes  # noqa: F401
from .validar import validar_llaves, validar_registro  # noqa: F401
