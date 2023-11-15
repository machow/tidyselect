import inspect

from functools import singledispatch
from typing import overload, TYPE_CHECKING


if TYPE_CHECKING:
    dispatch = overload
else:
    def dispatch(f):
        """Decorator for creating generic functions"""
        crnt = inspect.currentframe()
        outer = crnt.f_back

        if not f.__name__ in outer.f_locals:
            generic = singledispatch(f)
            generic._is_singledispatch = True
            return generic
        else:
            generic = outer.f_locals[f.__name__]
            if not getattr(generic, "_is_singledispatch"):
                raise ValueError(
                    f"Function {f.__name__} does not appear to be a generic function"
                )
            
            generic.register(f)

            return generic