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

from datetime import time
from zoneinfo import ZoneInfo

import pandas as pd
import functools

from pandas.tseries.offsets import CustomBusinessDay

from exchange_calendars.pandas_extensions.holiday import AbstractHolidayCalendar
from .tase_holidays import (
    FastDay,
    IndependenceDay,
    MemorialDay,
    NewYear,
    NewYear2,
    NewYearsEve,
    Passover,
    Passover2,
    PassoverInterimDay1,
    PassoverInterimDay1Before2026,
    PassoverInterimDay2,
    PassoverInterimDay2Before2026,
    PassoverInterimDay3,
    PassoverInterimDay3Before2026,
    PassoverInterimDay4,
    PassoverInterimDay4Before2026,
    SukkothInterimDay1,
    SukkothInterimDay1Before2026,
    SukkothInterimDay2,
    SukkothInterimDay2Before2026,
    SukkothInterimDay3,
    SukkothInterimDay3Before2026,
    SukkothInterimDay4,
    SukkothInterimDay4Before2026,
    SukkothInterimDay5,
    SukkothInterimDay5Before2026,
    Passover2Eve,
    PassoverEve,
    Pentecost,
    PentecostEve,
    Purim,
    SimchatTorah,
    SimchatTorahEve,
    Sukkoth,
    SukkothEve,
    YomKippur,
    YomKippurEve,
    YomKippurEveObserved,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar
from .pandas_extensions.offsets import MultipleWeekmaskCustomBusinessDay

# All holidays are defined as ad-hoc holidays for each year since there is
# currently no support for Hebrew calendar holiday rules in pandas.

HOLIDAY_EARLY_CLOSE = time(14, 15)
SUNDAY_CLOSE = time(15, 40)
FRIDAY_CLOSE = time(13, 50)


class SundayUntil2026(HolidayCalendar):
    def __init__(self):
        super().__init__(rules=[])

    def holidays(self, start=None, end=None, return_name=False):  # noqa: ARG002
        limit = pd.Timestamp("2026-01-05")
        if start is None:
            start = pd.Timestamp(AbstractHolidayCalendar.start_date)
        if end is None:
            end = pd.Timestamp(AbstractHolidayCalendar.end_date)
        effective_end = min(end, limit)
        if start > effective_end:
            return pd.DatetimeIndex([])
        return pd.date_range(start, effective_end, freq="W-SUN")


class FridayFrom2026(HolidayCalendar):
    def __init__(self):
        super().__init__(rules=[])

    def holidays(self, start=None, end=None, return_name=False):  # noqa: ARG002
        limit = pd.Timestamp("2026-01-05")
        if start is None:
            start = pd.Timestamp(AbstractHolidayCalendar.start_date)
        if end is None:
            end = pd.Timestamp(AbstractHolidayCalendar.end_date)
        effective_start = max(start, limit)
        if effective_start > end:
            return pd.DatetimeIndex([])
        return pd.date_range(effective_start, end, freq="W-FRI")


class XTAEExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for TASE Stock Exchange.

    Open/close times are continuous trading times valid Mon-Thu for Shares
    Group A. Trading schedule differs on Sundays.

    Open Time: 9:59 AM, Asia/Tel_Aviv (randomly between 9:59 and 10:00).
    Close Time: 5:15 PM, Asia/Tel_Aviv (randomly between 5:14 and 5:15).
    Friday close time: 1:50pm, Asia/Tel_Aviv

    Regularly-Observed Holidays (not necessarily in order):
    - Purim
    - Passover Eve
    - Passover
    - Passover II Eve
    - Passover II
    - Memorial Day
    - Independence Day
    - Pentecost Eve
    - Pentecost
    - Tisha B'Av
    - New Year's Eve
    - New Year
    - New Year II
    - Yom Kippur Eve
    - Yom Kippur
    - Sukkoth Eve
    - Sukkoth
    - Simchat Torah Eve
    - Simchat Torah

    Note these dates are only checked against 2019-2026.

    https://www.tase.co.il/en/content/knowledge_center/trading_vacation_schedule

    Daylight Saving Time in Israel comes into effect on the Friday before the
    last Sunday in March, and lasts until the last Sunday in October. During the
    Daylight Saving time period the clock will be UTC+3, and UTC+2 for the rest
    of the year.

    Transition to Monday-Friday Trading
    https://www.tase.co.il/en/content/about/tradingdays_change
    """

    name = "XTAE"

    tz = ZoneInfo("Asia/Tel_Aviv")

    open_times = ((None, time(9, 59)),)

    close_times = ((None, time(17, 15)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                Purim,
                PassoverEve,
                Passover,
                Passover2Eve,
                Passover2,
                MemorialDay,
                IndependenceDay,
                PentecostEve,
                Pentecost,
                FastDay,
                NewYearsEve,
                NewYear,
                NewYear2,
                YomKippurEve,
                YomKippurEveObserved,
                YomKippur,
                SukkothEve,
                Sukkoth,
                SimchatTorahEve,
                SimchatTorah,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [
            # Election days:
            # - 2019
            pd.Timestamp("2019-04-09"),
            pd.Timestamp("2019-09-17"),
            # - 2020
            pd.Timestamp("2020-03-02"),
            # - 2021
            pd.Timestamp("2021-03-23"),
            # - 2022
            pd.Timestamp("2022-11-01"),
        ]

    @property
    def special_closes(self):
        return [
            (
                HOLIDAY_EARLY_CLOSE,
                HolidayCalendar(
                    [
                        PassoverInterimDay1,
                        PassoverInterimDay2,
                        PassoverInterimDay3,
                        PassoverInterimDay4,
                        PassoverInterimDay1Before2026,
                        PassoverInterimDay2Before2026,
                        PassoverInterimDay3Before2026,
                        PassoverInterimDay4Before2026,
                        SukkothInterimDay1,
                        SukkothInterimDay2,
                        SukkothInterimDay3,
                        SukkothInterimDay4,
                        SukkothInterimDay5,
                        SukkothInterimDay1Before2026,
                        SukkothInterimDay2Before2026,
                        SukkothInterimDay3Before2026,
                        SukkothInterimDay4Before2026,
                        SukkothInterimDay5Before2026,
                    ]
                ),
            ),
            (SUNDAY_CLOSE, SundayUntil2026()),
            (FRIDAY_CLOSE, FridayFrom2026()),
        ]

    @property
    def special_weekmasks(self):
        """
        Returns
        -------
        list: List of (date, date, str) tuples that represent special
         weekmasks that applies between dates.
        """
        return [
            (None, pd.Timestamp("2026-01-04"), "1111001"),
        ]

    @functools.cached_property
    def day(self):
        if self.special_weekmasks:
            return MultipleWeekmaskCustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self.weekmask,
                weekmasks=self.special_weekmasks,
            )
        return CustomBusinessDay(
            holidays=self.adhoc_holidays,
            calendar=self.regular_holidays,
            weekmask=self.weekmask,
        )
