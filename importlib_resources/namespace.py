import os
import itertools
from ._compat import suppress, ZipPath, Path
from .abc import Traversable


def infer_path(path):
    return resolve_zip_path(path) or Path(path)


def resolve_zip_path(candidate, tail=''):
    if not candidate:
        return
    try:
        return ZipPath(candidate, at=tail)
    except Exception:
        new_tail = os.path.basename(candidate) + '/' + tail
        new_base = os.path.dirname(candidate)
        return resolve_zip_path(new_base, new_tail)


class Multiplexed(Traversable):
    """
    Given a series of Traversable objects, implement a merged
    version of the interface across all objects. Useful for
    namespace packages which may be multihomed at a single
    name.
    """
    @classmethod
    def load(cls, paths):
        return cls(map(cls._infer_path, paths))

    def __init__(self, *paths):
        self._paths = paths

    def iterdir(self):
        return itertools.chain.from_iterable(
            path.iterdir() for path in self._paths)

    def read_bytes(self):
        return self.open(mode='rb').read()

    def read_text(self, *args, **kwargs):
        return self.open(mode='r', *args, **kwargs).read()

    def is_dir(self):
        return any(path.is_dir() for path in self._paths)

    def is_file(self):
        return any(path.is_file() for path in self._paths)

    def joinpath(self, child):
        children = (
            path.joinpath(child)
            for path in self._paths
            )
        existing = (
            child
            for child in children
            if child.is_dir() or child.is_file()
            )
        return Multiplexed(*existing)

    __truediv__ = joinpath

    def open(self, *args, **kwargs):
        for path in self._paths[:-1]:
            with suppress(Exception):
                return path.open(*args, **kwargs)
        return self._paths[-1].open(*args, **kwargs)
