import pytest
import pandas as pd
import polars as pl
import siuba as sb

from tidyselect.eval_select import eval_select


params_frames = [pytest.param(pd.DataFrame, id="pandas"), pytest.param(pl.DataFrame, id="polars")]


@pytest.fixture(params=params_frames, scope="function")
def data(request) -> pd.DataFrame:
    return request.param({"ab": [1, 2, 3], "bc": ["a", "b", "c"], "xy": [4.0, 5.0, 6.0]})


def test_eval_select_siuba(data):
    from siuba import _

    res = eval_select(_.contains("b"), data)
    assert res == [("ab", 0), ("bc", 1)]


    res2 = eval_select(_["bc", "ab"], data)
    assert res2 == [("bc", 1), ("ab", 0)]


def test_eval_select_polars(data):
    import polars.selectors as cs

    if not isinstance(data, pl.DataFrame):
        pytest.xfail()

    res = eval_select(cs.contains("b"), data)
    assert res == [("ab", 0), ("bc", 1)]

    res2 = eval_select(["bc", "ab"], data)
    assert res2 == [("bc", 1), ("ab", 0)]

