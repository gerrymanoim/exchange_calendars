#
# Copyright 2018 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from datetime import time
import functools
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import Holiday
from pandas.tseries.offsets import CustomBusinessDay

from .exchange_calendar import HolidayCalendar
from .precomputed_exchange_calendar import PrecomputedExchangeCalendar
from .xkrx_holidays import (
    krx_regular_holiday_rules,
    precomputed_krx_holidays,
    precomputed_csat_days,
)
from .pandas_extensions.offsets import MultipleWeekmaskCustomBusinessDay
from .pandas_extensions.korean_holiday import next_business_day


class XKRXExchangeCalendar(PrecomputedExchangeCalendar):
    """
    Calendar for the Korea exchange, and the primary calendar for
    the country of South Korea.

    Open Time: 9:00 AM, KST (Korean Standard Time)
    Close Time: 3:30 PM, KST (Korean Standard Time)

    NOTE: Korea observes Standard Time year-round.

    Due to the complexity around the Korean holidays, we are hardcoding
    a list of holidays covering 1986-2019, inclusive.

    Regularly-Observed Holidays:
    - Seollal (New Year's Day)
    - Independence Movement Day
    - Labor Day
    - Buddha's Birthday
    - Memorial Day
    - Provincial Election Day
    - Liberation Day
    - Chuseok (Korean Thanksgiving)
    - National Foundation Day
    - Christmas Day
    - End of Year Holiday

    NOTE: Hangeul Day became a national holiday in 2013
    - Hangeul Proclamation Day
    """

    name = "XKRX"

    tz = ZoneInfo("Asia/Seoul")

    # KRX schedule change history
    # https://blog.naver.com/daishin_blog/220724111002

    # 1956-03-03: 0930~1130, 1330~1530
    # 1978-04-??: 1000~1200, 1330~1530
    # 1986-04-??: 0940~1200, 1320~1520
    # 1987-03-??: 0940~1140, 1320~1520
    # 1995-01-01: 0930~1130, 1300~1500
    # 1998-12-07: 0900~1200, 1300~1500
    # 2000-05-22: 0900~1500
    # 2016-08-01: 0900~1530

    # Break time disappears since 2000-05-22
    # https://www.donga.com/news/Economy/article/all/20000512/7534650/1

    # Closing time became 30mins late since 2016-08-01
    # https://biz.chosun.com/site/data/html_dir/2016/07/24/2016072400309.html

    open_times = (
        (None, time(9, 30)),
        (pd.Timestamp("1978-04-01"), time(10, 0)),
        (pd.Timestamp("1986-04-01"), time(9, 40)),
        (pd.Timestamp("1995-01-01"), time(9, 30)),
        (pd.Timestamp("1998-12-07"), time(9, 0)),
    )
    break_start_times = (
        (None, time(11, 30)),
        (pd.Timestamp("1978-04-01"), time(12, 0)),
        (pd.Timestamp("1987-03-01"), time(11, 40)),
        (pd.Timestamp("1995-01-01"), time(11, 30)),
        (pd.Timestamp("1998-12-07"), time(12, 0)),
        (pd.Timestamp("2000-05-22"), None),
    )
    break_end_times = (
        (None, time(13, 30)),
        (pd.Timestamp("1986-04-01"), time(13, 20)),
        (pd.Timestamp("1995-01-01"), time(13, 0)),
        (pd.Timestamp("2000-05-22"), None),
    )
    close_times = (
        (None, time(15, 30)),
        (pd.Timestamp("1986-04-01"), time(15, 20)),
        (pd.Timestamp("1995-01-01"), time(15, 0)),
        (pd.Timestamp("2016-08-01"), time(15, 30)),
    )

    # Saterday became holiday since 1998-12-07
    # https://www.hankyung.com/finance/article/1998080301961

    weekmask = "1111100"

    @property
    def special_weekmasks(self):
        """
        Returns
        -------
        list: List of (date, date, str) tuples that represent special
         weekmasks that applies between dates.
        """
        return [
            (None, pd.Timestamp("1998-12-06"), "1111110"),
        ]

    @classmethod
    def precomputed_holidays(cls) -> list[pd.Timestamp]:
        return precomputed_krx_holidays.tolist()

    @classmethod
    def _earliest_precomputed_year(cls) -> int:
        return 1956

    @classmethod
    def _latest_precomputed_year(cls) -> int:
        return 2050

    # KRX regular and precomputed adhoc holidays

    @property
    def regular_holidays(self):
        return HolidayCalendar(krx_regular_holiday_rules)

    # The first business day of each year:
    #  opening schedule is delayed by an hour.

    @property
    def special_offsets(self):
        """
        Returns
        -------
        list: List of (timedelta, timedelta, timedelta, timedelta, AbstractHolidayCalendar) tuples
         that represent special open, break_start, break_end, close offsets
         and corresponding HolidayCalendars.
        """
        return [
            (
                pd.Timedelta(1, unit="h"),
                None,
                None,
                None,
                HolidayCalendar(
                    [
                        Holiday(
                            "First Business Day of Year",
                            month=1,
                            day=1,
                            observance=next_business_day,
                        )
                    ]
                ),
            ),
        ]

    # Every year's CSAT day, all schedules are delayed by:
    #  before 1998-11-18: 30 minutes
    #  after  1998-11-18: 1 hour

    @property
    def special_offsets_adhoc(
        self,
    ) -> list[
        tuple[pd.Timedelta, pd.Timedelta, pd.Timedelta, pd.Timedelta, pd.DatetimeIndex]
    ]:
        """
        Returns
        -------
        list: List of (timedelta, timedelta, timedelta, timedelta, DatetimeIndex) tuples
         that represent special open, break_start, break_end, close offsets
         and corresponding DatetimeIndexes.
        """
        return [
            (
                pd.Timedelta(30, unit="m"),
                pd.Timedelta(30, unit="m"),
                pd.Timedelta(30, unit="m"),
                pd.Timedelta(30, unit="m"),
                precomputed_csat_days[
                    precomputed_csat_days.slice_indexer("1993-08-20", "1998-11-17")
                ],
            ),
            (
                pd.Timedelta(1, unit="h"),
                pd.Timedelta(1, unit="h"),
                pd.Timedelta(1, unit="h"),
                pd.Timedelta(1, unit="h"),
                precomputed_csat_days[
                    precomputed_csat_days.slice_indexer("1998-11-18", None)
                ],
            ),
        ]

    def _overwrite_special_offsets(
        self,
        session_labels: pd.DatetimeIndex,
        standard_times: pd.DatetimeIndex | None,
        offsets: tuple[pd.Timedelta, HolidayCalendar],
        ad_hoc_offsets: tuple[pd.Timedelta, pd.DatetimeIndex],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        strict: bool = False,
    ):
        # Short circuit when nothing to apply.
        if standard_times is None or not len(standard_times):
            return

        len_m, len_oc = len(session_labels), len(standard_times)
        if len_m != len_oc:
            raise ValueError(
                "Found misaligned dates while building calendar.\nExpected"
                " session_labels to be the same length as open_or_closes but,\n"
                f"len(session_labels)={len_m}, len(open_or_closes)={len_oc}"
            )

        regular = []
        for offset, calendar in offsets:
            days = calendar.holidays(start_date, end_date)
            series = pd.Series(index=days, data=offset)
            regular.append(series)

        ad_hoc = []
        for offset, datetimes in ad_hoc_offsets:
            series = pd.Series(index=datetimes, data=offset)
            ad_hoc.append(series)

        merged = regular + ad_hoc
        if not merged:
            return pd.Series([], dtype="timedelta64[ns]")

        result = pd.concat(merged).sort_index()
        offsets = result.loc[(result.index >= start_date) & (result.index <= end_date)]

        # Find the array indices corresponding to each special date.
        indexer = session_labels.get_indexer(offsets.index)

        # -1 indicates that no corresponding entry was found.  If any -1s are
        # present, then we have special dates that doesn't correspond to any
        # trading day.
        if -1 in indexer and strict:
            bad_dates = list(offsets.index[indexer == -1])
            raise ValueError(f"Special dates {bad_dates} are not trading days.")

        special_opens_or_closes = standard_times[indexer] + offsets

        # Short circuit when nothing to apply.
        if not len(special_opens_or_closes):
            return

        # NOTE: This is a slightly dirty hack.  We're in-place overwriting the
        # internal data of an Index, which is conceptually immutable.  Since we're
        # maintaining sorting, this should be ok, but this is a good place to
        # sanity check if things start going haywire with calendar computations.
        standard_times.values[indexer] = special_opens_or_closes.values

    def apply_special_offsets(
        self,
        session_labels: pd.DatetimeIndex,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ):
        """Evaluate and overwrite special offsets."""
        _special_offsets = self.special_offsets
        _special_offsets_adhoc = self.special_offsets_adhoc

        _special_open_offsets = [
            (t[0], t[-1]) for t in _special_offsets if t[0] is not None
        ]
        _special_open_offsets_adhoc = [
            (t[0], t[-1]) for t in _special_offsets_adhoc if t[0] is not None
        ]
        _special_break_start_offsets = [
            (t[1], t[-1]) for t in _special_offsets if t[1] is not None
        ]
        _special_break_start_offsets_adhoc = [
            (t[1], t[-1]) for t in _special_offsets_adhoc if t[1] is not None
        ]
        _special_break_end_offsets = [
            (t[2], t[-1]) for t in _special_offsets if t[2] is not None
        ]
        _special_break_end_offsets_adhoc = [
            (t[2], t[-1]) for t in _special_offsets_adhoc if t[2] is not None
        ]
        _special_close_offsets = [
            (t[3], t[-1]) for t in _special_offsets if t[3] is not None
        ]
        _special_close_offsets_adhoc = [
            (t[3], t[-1]) for t in _special_offsets_adhoc if t[3] is not None
        ]

        self._overwrite_special_offsets(
            session_labels,
            self._opens,
            _special_open_offsets,
            _special_open_offsets_adhoc,
            start,
            end,
        )
        self._overwrite_special_offsets(
            session_labels,
            self._break_starts,
            _special_break_start_offsets,
            _special_break_start_offsets_adhoc,
            start,
            end,
        )
        self._overwrite_special_offsets(
            session_labels,
            self._break_ends,
            _special_break_end_offsets,
            _special_break_end_offsets_adhoc,
            start,
            end,
        )
        self._overwrite_special_offsets(
            session_labels,
            self._closes,
            _special_close_offsets,
            _special_close_offsets_adhoc,
            start,
            end,
        )

    @functools.cached_property
    def day(self):
        if self.special_weekmasks:
            return MultipleWeekmaskCustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self.weekmask,
                weekmasks=self.special_weekmasks,
            )
        else:
            return CustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self.weekmask,
            )


class PrecomputedXKRXExchangeCalendar(PrecomputedExchangeCalendar):
    """
    Calendar for the Korea exchange, and the primary calendar for
    the country of South Korea.

    Open Time: 9:00 AM, KST (Korean Standard Time)
    Close Time: 3:30 PM, KST (Korean Standard Time)

    NOTE: Korea observes Standard Time year-round.

    Due to the complexity around the Korean holidays, we are hardcoding
    a list of holidays covering 1986-2019, inclusive.

    Regularly-Observed Holidays:
    - Seollal (New Year's Day)
    - Independence Movement Day
    - Labor Day
    - Buddha's Birthday
    - Memorial Day
    - Provincial Election Day
    - Liberation Day
    - Chuseok (Korean Thanksgiving)
    - National Foundation Day
    - Christmas Day
    - End of Year Holiday

    NOTE: Hangeul Day became a national holiday in 2013
    - Hangeul Proclamation Day
    """

    name = "XKRX"

    tz = ZoneInfo("Asia/Seoul")

    open_times = ((None, time(9)),)
    close_times = ((None, time(15, 30)),)

    @classmethod
    def precomputed_holidays(cls):
        return precomputed_krx_holidays
