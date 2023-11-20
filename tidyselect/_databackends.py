# Databackend ----
# Copied from https://github.com/machow/databackend

import sys
import importlib

from abc import ABCMeta


def _load_class(mod_name: str, cls_name: str):
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


class _AbstractBackendMeta(ABCMeta):
    def register_backend(cls, mod_name: str, cls_name: str):
        cls._backends.append((mod_name, cls_name))
        cls._abc_caches_clear()


class AbstractBackend(metaclass=_AbstractBackendMeta):
    @classmethod
    def __init_subclass__(cls):
        if not hasattr(cls, "_backends"):
            cls._backends = []

    @classmethod
    def __subclasshook__(cls, subclass):
        for mod_name, cls_name in cls._backends:
            if mod_name not in sys.modules:
                # module isn't loaded, so it can't be the subclass
                # we don't want to import the module to explicitly run the check
                # so skip here.
                continue
            else:
                parent_candidate = _load_class(mod_name, cls_name)
                if issubclass(subclass, parent_candidate):
                    return True

        return NotImplemented


# Implementations ----

from typing import TYPE_CHECKING, Union  # noqa


if TYPE_CHECKING:
    from pandas import DataFrame as PdDataFrame, Series as PdSeries
    from polars import DataFrame as PlDataFrame, Series as PlSeries
    from polars import Expr as PlExpr
    from siuba.siu import Call, Symbolic

    SbLazy = Union[Call, Symbolic]
    ColumnLike = Union[PdSeries, PlSeries]
else:

    class PdDataFrame(AbstractBackend):
        _backends = [("pandas", "DataFrame")]

    class PlDataFrame(AbstractBackend):
        _backends = [("polars", "DataFrame")]

    class PlExpr(AbstractBackend):
        _backends = [("polars", "Expr")]

    class SbLazy(AbstractBackend):
        _backends = [("siuba.siu", "Call"), ("siuba.siu", "Symbolic")]
