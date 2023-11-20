import pytest

import tidyselect.selectors as sel


PARAMS = [(sel.starts_with, [1]), (sel.ends_with, [0]), (sel.contains, [0, 1])]


@pytest.mark.parametrize("func, dst", PARAMS)
def test_selectors_eager(func, dst):
    res = func(sel.Names(["ab", "bc", "xy"]), "b")

    assert res == sel.NamesMatch(dst)


@pytest.mark.parametrize("func, dst", PARAMS)
def test_selectors_var_ops(func, dst):
    op = func("b")

    assert op.eval(["ab", "bc", "xy"]) == sel.NamesMatch(dst)


def test_selectors_and():
    op = sel.starts_with("a") & sel.ends_with("b")

    assert op.eval(["ab", "bb", "xy"]) == sel.NamesMatch([0])


def test_selectors_or():
    op = sel.starts_with("a") | sel.ends_with("b")

    assert op.eval(["ab", "bb", "xy"]) == sel.NamesMatch([0, 1])


def test_selectors_c_strings():
    op = sel.c("ab", "xy")

    assert op.eval(["ab", "bb", "xy"]) == sel.NamesMatch([0, 2])


def test_selectors_c_selectors():
    op = sel.c(sel.starts_with("a"), sel.ends_with("b"))

    assert op.eval(["ab", "bb", "xy"]) == sel.NamesMatch([0, 1])


def test_selectors_invert():
    op = ~sel.c("ab")
    assert op.eval(["ab", "bb", "xy"]) == sel.NamesMatch([1, 2])
