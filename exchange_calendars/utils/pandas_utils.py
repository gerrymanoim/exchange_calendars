from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from exchange_calendars.calendar_helpers import UTC


def days_at_time(
    dates: pd.DatetimeIndex,
    time: datetime.time | None,
    tz: ZoneInfo,
    day_offset: int,
) -> pd.DatetimeIndex:
    """Return UTC DatetimeIndex of given dates at a given time.

    Parameters
    ----------
    dates
        Dates or date (timezone naive with no time component).

    time
        The time to apply as an offset to each day in `dates`.

    tz
        The timezone in which to interpret `time`.

    day_offset
        Number of days by which to offset each date in `dates`.

    Returns
    -------
    pd.DatetimeIndex
        DatetimeIndex comprising Timestamp evaluted from `dates` and `time`
        with `dates` offset by `day_offset` and `time` interpreted as having
        timezone `tz`. DatetimeIndex has UTC timezone.

    Examples
    --------
    In the example below, the times switch from 13:45 to 12:45 UTC because
    March 13th is the daylight savings transition for America/New_York. All
    the times are still 8:45 when interpreted in America/New_York.

    >>> import pandas as pd; import datetime; import pprint
    >>> dts = pd.date_range('2016-03-12', '2016-03-14')
    >>> dts_845 = days_at_time(dts, datetime.time(8, 45), 'America/New_York', 0)
    >>> pprint.pprint([str(dt) for dt in dts_845])
    ['2016-03-12 13:45:00+00:00',
     '2016-03-13 12:45:00+00:00',
     '2016-03-14 12:45:00+00:00']
    """
    if time is None:
        return pd.DatetimeIndex([None for _ in dates]).tz_localize(UTC)

    if len(dates) == 0:
        return dates.tz_localize(UTC)

    # Offset days without tz to avoid timezone issues.
    delta = pd.Timedelta(
        days=day_offset,
        hours=time.hour,
        minutes=time.minute,
        seconds=time.second,
    )
    return (dates + delta).tz_localize(tz).tz_convert(UTC)


def vectorized_sunday_to_monday(dtix):
    """A vectorized implementation of
    :func:`pandas.tseries.holiday.sunday_to_monday`.

    Parameters
    ----------
    dtix : pd.DatetimeIndex
        The index to shift sundays to mondays.

    Returns
    -------
    sundays_as_mondays : pd.DatetimeIndex
        ``dtix`` with all sundays moved to the next monday.
    """
    values = dtix.values.copy()
    values[dtix.weekday == 6] += np.timedelta64(1, "D")
    return pd.DatetimeIndex(values)


def longest_run(ser: pd.Series) -> pd.Index:
    """Get the longest run of consecutive True values in a Series.

    Function can be used to find the longest run of values that meet a
    condition.

    Parameters
    ----------
    ser
        pd.Series of bool dtype.
            Index should reflect values against which a condition was
                assessed.
            Values should reflect whether corresponding index value
                met the condition.

    Return
    ------
    pd.Index
        Slice of `ser` index that corresponds with the longest run of
            consecutive True values.

    Examples
    --------
    >>> arr = np.arange(0, 88)
    >>> ser = pd.Series(arr, index=arr)
    >>> bv = (
    ...     ((ser >= 10) & (ser < 16))
    ...     | ((ser >= 30) & (ser <= 40))
    ...     | ((ser >= 55) & (ser < 61))
    ... )
    >>> longest_run(bv)
    Index([30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40], dtype='int32')
    >>> pd.testing.assert_index_equal(longest_run(bv), ser.index[30:41])
    """
    # group Trues by only adding to sum when value False.
    trues_grouped = (~ser).cumsum()[ser]  # and only take True Values
    group_sizes = trues_grouped.value_counts()  # count each run
    max_run_size = group_sizes.max()
    max_run_group_id = group_sizes[group_sizes == max_run_size].index[0]
    run = trues_grouped[trues_grouped == max_run_group_id].index
    return run


def indexes_union(indexes: list[pd.Index]) -> pd.Index:
    """Return union of multiple pd.Index objects.

    Parameters
    ----------
    indexes
        Index objects to be joined. All indexes must be of same dtype.

    Examples
    --------
    >>> index1 = pd.date_range('2021-05-01 12:20', periods=2, freq='1h')
    >>> index2 = pd.date_range('2021-05-02 17:10', periods=2, freq='22min')
    >>> index3 = pd.date_range('2021-05-03', periods=2, freq='1D')
    >>> indexes_union([index1, index2, index3])
    DatetimeIndex(['2021-05-01 12:20:00', '2021-05-01 13:20:00',
                   '2021-05-02 17:10:00', '2021-05-02 17:32:00',
                   '2021-05-03 00:00:00', '2021-05-04 00:00:00'],
                  dtype='datetime64[ns]', freq=None)
    """
    index = indexes[0]
    for indx in indexes[1:]:
        index = index.union(indx)
    return index
