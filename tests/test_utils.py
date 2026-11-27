import inspect

import pandas as pd
import pandas.testing as tm
import pytest


def T(x):  # noqa: N802
    return pd.Timestamp(x)


# NOTE `check_freq` is a parameter of `tm.assert_index_equal` from pandas 3.1. When the
# minimum supported version of pandas bumps to 3.1, calls to `assert_index_equal_compat`
# can be replaced with calls to `tm.assert_index_equal`.
_TAKES_CHECK_FREQ = "check_freq" in inspect.signature(tm.assert_index_equal).parameters


def assert_index_equal_compat(
    left: pd.Index, right: pd.Index, *, check_freq: bool, **kwargs
) -> None:
    """Assert that two indexes are equal.

    The `freq` attributes are checked if `check_freq` is True. `check_freq` has the
    same effect on every supported version of pandas.

    Parameters
    ----------
    left
        Index to compare with `right`.
    right
        Index to compare with `left`.
    check_freq
        Whether to check that `left.freq` is equal to `right.freq`. The check is made
        only if both indexes are a DatetimeIndex or a TimedeltaIndex and `check_order`
        is True. pandas 3.1 makes the check under the same condition.
    **kwargs
        Passed to `tm.assert_index_equal`.
    """
    __tracebackhide__ = True
    if _TAKES_CHECK_FREQ:
        tm.assert_index_equal(left, right, check_freq=check_freq, **kwargs)
        return
    tm.assert_index_equal(left, right, **kwargs)
    freq_types = (pd.DatetimeIndex, pd.TimedeltaIndex)
    if (
        check_freq
        and kwargs.get("check_order", True)
        and isinstance(left, freq_types)
        and isinstance(right, freq_types)
    ):
        assert left.freq == right.freq, f"freqs differ: {left.freq!r}, {right.freq!r}"


def test_assert_index_equal_compat():
    left = pd.date_range("2021-01-04", periods=3, freq="D")
    right = pd.DatetimeIndex(left.to_numpy())
    assert right.freq is None
    assert_index_equal_compat(left, right, check_freq=False)
    with pytest.raises(AssertionError):
        assert_index_equal_compat(left, right, check_freq=True)
