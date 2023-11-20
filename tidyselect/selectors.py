from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Union
from typing_extensions import Concatenate, ParamSpec, Self, TypeVar
from ._dispatch import dispatch


# Types ----

P = ParamSpec("P")
T = TypeVar("T")
OperationFunction = Callable[Concatenate["Names", P], "NamesMatch"]
OperationPredicate = Callable[[Any], bool]


# Misc ----
class NoArgs:
    """Represent first argument to generic called without arguments."""


def support_no_args(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Case 1: no arguments -----
        if not len(args):
            return f(NoArgs(), *args, **kwargs)

        return f(*args, **kwargs)

    return wrapped


# Data ----


class Names(list[str]):
    """A list of names."""


class NamesMatch(list[int]):
    """A list of integers corresponding to a selection."""

    def __and__(self, rhs: NamesMatch) -> Self:
        # maintains order based on left-hand side
        rhs_set = set(rhs)
        return NamesMatch([pos for pos in self if pos in rhs_set])

    def __or__(self, rhs: NamesMatch) -> Self:
        lhs_set = set(self)
        return NamesMatch([*self, *(el for el in rhs if el not in lhs_set)])

    def __invert__(self):
        # TODO: if we kept the max length, we could invert.
        raise NotImplementedError("Cannot invert a NamesMatch directly.")


# Var classes -----------------------------------------------------------------


class VarBase:
    """Basic selection class."""

    def eval(self, names: list[str]) -> NamesMatch:
        raise NotImplementedError()


class VarOperation(VarBase):
    """A selection operation."""

    expr: OperationFunction

    def eval(self, names: list[str]) -> NamesMatch:
        """Return a boolean list of matching names.

        Parameters
        ----------
        names:
            Names to select from.
        """
        return self.expr(Names(names))

    def __and__(self, x: "VarOperation"):
        return VarOperationAnd(self, x)

    def __or__(self, x: "VarOperation"):
        return VarOperationOr(self, x)

    def __invert__(self) -> VarOperationInvert:
        return VarOperationInvert(self)


class VarList(VarOperation):
    """A list of selectors."""

    entries: tuple[VarOperation | str, ...]

    def __init__(self, entries):
        self.entries = entries

    def eval(self, names: list[str]) -> NamesMatch:
        """Return a boolean list of matching names."""
        if self.entries:
            crnt_res = self._eval_entry(self.entries[0], names)

            for entry in self.entries[1:]:
                if isinstance(entry, str):
                    crnt_res = crnt_res | NamesMatch(
                        [ii for ii, name in enumerate(names) if name == entry]
                    )
                else:
                    crnt_res = crnt_res | self._eval_entry(entry, names)

            return crnt_res

        return NamesMatch([])

    @staticmethod
    def _eval_entry(entry: str | VarOperation, names: list[str]) -> NamesMatch:
        if isinstance(entry, str):
            return NamesMatch([ii for ii, name in enumerate(names) if name == entry])

        return entry.eval(names)


class VarPredicate(VarBase):
    """A selection predicate."""

    expr: OperationPredicate

    def __init__(self, expr: OperationPredicate):
        self.expr = expr

    def eval(self, columns: list[Any]) -> NamesMatch:
        """Return a boolean list of matching names, based on data.

        Parameters
        ----------
        names:
            Names to select from.
        """
        return NamesMatch([ii for ii, col in enumerate(columns) if self.expr(col)])


# VarOperation classes -------------------------------------------------------


class VarOperationFunc(VarOperation):
    """A selection operation."""

    def __init__(
        self, expr: OperationFunction, args: tuple = tuple(), kwargs: dict | None = None
    ):
        self.expr = expr
        self.args = args
        self.kwargs = {} if kwargs is None else kwargs

    def eval(self, names: list[str]) -> NamesMatch:
        """Return a boolean list of matching names.

        Parameters
        ----------
        names:
            Names to select from.
        """
        return self.expr(Names(names), *self.args, **self.kwargs)


class VarOperationAnd(VarOperation):
    def __init__(self, lhs: VarOperation, rhs: VarOperation):
        self.lhs = lhs
        self.rhs = rhs

    def expr(self, names: list[str]) -> NamesMatch:
        # maintains order based on left-hand side
        res_lhs = self.lhs.eval(names)
        res_rhs = self.rhs.eval(names)

        return res_lhs & res_rhs


class VarOperationOr(VarOperation):
    def __init__(self, lhs: VarOperation, rhs: VarOperation):
        self.lhs = lhs
        self.rhs = rhs

    def expr(self, names: list[str]) -> NamesMatch:
        lhs_pos = self.lhs.eval(names)
        rhs_pos = self.rhs.eval(names)

        return lhs_pos | rhs_pos


class VarOperationInvert(VarOperation):
    def __init__(self, op: VarOperation):
        self.op = op

    def expr(self, names: list[str]) -> NamesMatch:
        to_exclude = set(self.op.eval(names))
        return NamesMatch([ii for ii, _ in enumerate(names) if ii not in to_exclude])


# VarPredicate classes ---------------------------------------------------------


# selector functions -----------------------------------------------------------

# c ----


# TODO: should type : str | VarOperation
# but because we have singledispatch register based on annotation, and
# it expects a single type, it's having a bad time.
@dispatch
def c(*args: Union[str, VarOperation]) -> VarList:
    """Combine a series of selectors."""

    return VarList(args)


@dispatch
def c(self: Names, *args: Union[str, VarOperation]) -> NamesMatch:
    """Combine a series of selectors."""

    return VarList(args).eval(self)


# starts_with ----


@dispatch
def starts_with(x: str) -> VarOperationFunc:
    """Select variables starting with a prefix.

    Parameters
    ----------
    x:
        Prefix to match.

    Notes
    -----
    If passed a Names object, then this returns a list of integers corresponding
    to the matching names. Otherwise, it returns a VarOperation object.
    """

    return VarOperationFunc(starts_with, (x,))


@dispatch
def starts_with(self: Names, x: str) -> NamesMatch:
    return NamesMatch([ii for ii, name in enumerate(self) if name.startswith(x)])


# ends_with ----


@dispatch
def ends_with(x: str) -> VarOperationFunc:
    """Select variables ending with a prefix."""

    return VarOperationFunc(ends_with, (x,))


@dispatch
def ends_with(self: Names, x: str) -> NamesMatch:
    return NamesMatch([ii for ii, name in enumerate(self) if name.endswith(x)])


# contains ----


@dispatch
def contains(x: str) -> VarOperationFunc:
    """Select variables containing a substring."""

    return VarOperationFunc(contains, (x,))


@dispatch
def contains(self: Names, x: str) -> NamesMatch:
    return NamesMatch([ii for ii, name in enumerate(self) if x in name])


# everything ----


@support_no_args
@dispatch
def everything(data=NoArgs) -> VarOperationFunc:
    """Select all variables."""

    return VarOperationFunc(everything)


@dispatch
def everything(self: Names) -> NamesMatch:
    return NamesMatch(list(range(len(self))))


# where ----

# TODO: should type : Callable[[ColumnLike], bool]


def where(predicate) -> VarPredicate:
    """Select variables based on a predicate.

    Parameters
    ----------
    predicate:
        A function that takes a column and returns a boolean.
    """

    return VarPredicate(predicate)
