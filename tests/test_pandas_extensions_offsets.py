"""Tests for the custom pandas offsets in exchange_calendars.pandas_extensions.offsets.

pandas 3.1 renamed the scalar offset hooks (`_apply` -> `_add_datetime`,
`_apply_array` -> `_add_datetime_ndarray`) and added a vectorized `date_range` path
for CustomBusinessDay-like offsets; these tests pin that array arithmetic and
`date_range` agree with the scalar logic whichever pandas is installed.
"""

import pandas as pd
import pytest

from exchange_calendars.pandas_extensions.offsets import (
    MultipleWeekmaskCustomBusinessDay,
    OrthodoxEaster,
)


class TestOrthodoxEaster:
    @pytest.mark.parametrize("n", [-2, -1, 0, 1, 2])
    def test_index_addition_matches_scalar_addition(self, n):
        offset = OrthodoxEaster(n)
        # Orthodox Easter 2024 is 2024-05-05 and 2025 is 2025-04-20.
        stamps = pd.DatetimeIndex(
            [
                "2023-01-01",
                "2024-05-04",
                "2024-05-05",
                "2024-05-05 13:30",
                "2024-05-06",
                "2025-04-20",
                "2025-12-31 23:59:59",
            ]
        )
        expected = pd.DatetimeIndex([stamp + offset for stamp in stamps])
        pd.testing.assert_index_equal(stamps + offset, expected)

    def test_series_addition_works(self):
        result = (
            pd.Series(pd.to_datetime(["2024-01-01", "2024-06-01"])) + OrthodoxEaster()
        )
        assert list(result) == [pd.Timestamp("2024-05-05"), pd.Timestamp("2025-04-20")]


class TestMultipleWeekmaskCustomBusinessDay:
    @pytest.fixture
    def offset(self):
        # A Sunday is a working day in the weeks of 2024-01-08 and 2024-02-05;
        # every other week is Monday to Friday.
        weeks = [
            (pd.Timestamp("2024-01-08"), pd.Timestamp("2024-01-14"), "1111101"),
            (pd.Timestamp("2024-02-05"), pd.Timestamp("2024-02-11"), "1111101"),
        ]
        return MultipleWeekmaskCustomBusinessDay(
            weekmask="Mon Tue Wed Thu Fri", weekmasks=weeks, holidays=[]
        )

    def test_date_range_includes_the_working_sundays(self, offset):
        sessions = pd.date_range("2024-01-01", "2024-02-29", freq=offset)
        assert pd.Timestamp("2024-01-14") in sessions
        assert pd.Timestamp("2024-02-11") in sessions
        assert pd.Timestamp("2024-01-21") not in sessions

    def test_index_addition_matches_scalar_addition(self, offset):
        stamps = pd.DatetimeIndex(
            ["2024-01-12", "2024-01-13", "2024-01-14", "2024-02-09", "2024-02-10"]
        )
        expected = pd.DatetimeIndex([stamp + offset for stamp in stamps])
        pd.testing.assert_index_equal(stamps + offset, expected)
