"""cogeo-mosaic File backend."""

import json
import pathlib

import attr
from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from cogeo_mosaic.backends.base import BaseBackend
from cogeo_mosaic.backends.utils import _compress_gz_json, _decompress_gz
from cogeo_mosaic.cache import cache_config
from cogeo_mosaic.errors import _FILE_EXCEPTIONS, MosaicError, MosaicExistsError
from cogeo_mosaic.mosaic import MosaicJSON


@attr.s
class FileBackend(BaseBackend):
    """Local File Backend Adapter"""

    _backend_name = "File"

    def write(self, overwrite: bool = False):
        """Write mosaicjson document to a file."""
        if not overwrite and pathlib.Path(self.path).exists():
            raise MosaicExistsError("Mosaic file already exist, use `overwrite=True`.")

        body = self.mosaic_def.dict(exclude_none=True)
        with open(self.path, "wb") as f:
            try:
                if self.path.endswith(".gz"):
                    f.write(_compress_gz_json(body))
                else:
                    f.write(json.dumps(body).encode("utf-8"))
            except Exception as e:
                exc = _FILE_EXCEPTIONS.get(e, MosaicError)  # type: ignore
                raise exc(str(e)) from e

    @cached(
        TTLCache(maxsize=cache_config.maxsize, ttl=cache_config.ttl),
        key=lambda self: hashkey(self.path),
    )
    def _read(self) -> MosaicJSON:  # type: ignore
        """Get mosaicjson document."""
        try:
            with open(self.path, "rb") as f:
                body = f.read()
        except Exception as e:
            exc = _FILE_EXCEPTIONS.get(e, MosaicError)  # type: ignore
            raise exc(str(e)) from e

        self._file_byte_size = len(body)

        if self.path.endswith(".gz"):
            body = _decompress_gz(body)

        return MosaicJSON(**json.loads(body))
