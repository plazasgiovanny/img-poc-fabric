"""Biblioteca común de la PoC IMG (§18: lectura de parámetros vigentes, validaciones,
bitácora de ejecución y escritura estandarizada). Sin dependencias duras: el núcleo es
Python puro; las funciones que tocan Spark/Delta importan `pyspark` de forma diferida."""

__version__ = "0.1.0"

from .fingerprint import sha256_bytes, sha256_file  # noqa: F401
from . import mapping  # noqa: F401
from .normalize import (  # noqa: F401
    normalize_date,
    normalize_doc_number,
    normalize_doc_type,
    normalize_locality,
    normalize_name,
)
from .params import active  # noqa: F401
from .validate import validate_keys, validate_record  # noqa: F401
