from collections.abc import Mapping
from typing import Any, Type, Union

from ._databackends import PdDataFrame, PlDataFrame, PlExpr, SbLazy
from ._dispatch import dispatch

DataLike = Union[PdDataFrame, PlDataFrame, Mapping]

# Utils -----------------------------------------------------------------------

def get_names(data) -> list[str]:
    if isinstance(data, PlDataFrame):
        return data.columns
    elif isinstance(data, PdDataFrame):
        return list(data.columns)
    elif isinstance(data, Mapping):
        return list(data.keys())

    raise TypeError(f"Unsupported data type: {type(data)}")


# expr_style -----

class UnknownStyle:
    """Represent an unknown expression style."""

@dispatch
def expr_style(expr) -> Type[UnknownStyle]:
    return UnknownStyle


@dispatch
def expr_style(expr: SbLazy) -> Type[SbLazy]:
    return SbLazy


@dispatch
def expr_style(expr: PlExpr) -> Type[PlExpr]:
    return PlExpr





# eval_select -----------------------------------------------------------------

@dispatch
def eval_select(expr, data: DataLike):
    """Evaluate a select expression with tidyselect semantics

    Parameters
    ----------
    expr:
        An object describing selection.
    data:
        Data names are selected from. Generally a DataFrame or dictionary, though 
        anything with `keys()`, and `__getitem__()` methods is supported.
    """

    raise NotImplementedError()


@dispatch
def eval_select(expr: str, data: DataLike):
    if expr in get_names(data):
        return [(expr, 0)]
 
    return []


@dispatch
def eval_select(expr: SbLazy, data: DataLike):
    from siuba.dply.tidyselect import var_select, var_create
    from siuba.siu import strip_symbolic

    names = get_names(data)
    var_expr = var_create(strip_symbolic(expr))
    res_col_names = var_select(names, *var_expr)

    # TODO: this assumes no duplicate column names
    return [(x, names.index(x)) for x in res_col_names]


@dispatch
def eval_select(expr: PlExpr, data: DataLike):
    from polars.selectors import _selector_proxy_

    # Note that currently a list is supported, since list dispatching
    # punts to here.
    if not isinstance(expr, (list, _selector_proxy_)):
        raise TypeError("Expected a polars selector expression.")

    if not isinstance(data, PlDataFrame):
        raise TypeError("Can only use a polars selector on a polars DataFrame")
    
    names = get_names(data)
    res_col_names = data.select(expr).columns

    return [(x, names.index(x)) for x in res_col_names]


@dispatch
def eval_select(expr: list, data: DataLike):
    for entry in expr:
        cls_style = expr_style(entry)
        if cls_style is not UnknownStyle:
            return eval_select.dispatch(cls_style)(expr, data)
    
    return _eval_select_default(data, expr)


# _eval_select_default --------------------------------------------------------

@dispatch
def _eval_select_default(data: DataLike, expr):
    raise NotImplementedError(f"Unsupported data type: {type(data)}")


@dispatch
def _eval_select_default(data: PlDataFrame, expr):
    return eval_select.dispatch(PlExpr)(expr, data)
