#
# Copyright 2019 Quantopian, Inc.
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

import datetime
from itertools import chain
from zoneinfo import ZoneInfo
import pandas as pd
import functools

from pandas.tseries.holiday import Holiday, weekend_to_monday
from pandas.tseries.offsets import CustomBusinessDay

from .common_holidays import european_labour_day, new_years_day, new_years_eve
from .exchange_calendar import WEEKDAYS, HolidayCalendar, ExchangeCalendar
from .pandas_extensions.offsets import MultipleWeekmaskCustomBusinessDay


def new_years_eve_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # For some reason New Year's Eve was not a holiday these years.
    return None if dt.year in [2008, 2009] else weekend_to_monday(dt)


def new_years_day_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # New Year's Day did not follow the next-non-holiday rule these years.
    return None if dt.year in [2022] else weekend_to_monday(dt)


def new_years_holiday_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # New Year's Holiday did not follow the next-non-holiday rule these years.
    return None if dt.year in [2016, 2021, 2022] else weekend_to_monday(dt)


def orthodox_christmas_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # Orthodox Christmas did not follow the next-non-holiday rule these years.
    return None if dt.year in [2012, 2017, 2023, 2024] else weekend_to_monday(dt)


def defender_of_fatherland_observance(
    dt: datetime.datetime,
) -> datetime.datetime | None:
    # Defender of the Fatherland Day did not follow the next-non-holiday rule
    # these years.
    return None if dt.year in [2013, 2014, 2019] else weekend_to_monday(dt)


def victory_day_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # Victory Day did not follow the next-non-holiday rule these years.
    return None if dt.year in [2021] else weekend_to_monday(dt)


def day_of_russia_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # Day of Russia did not follow the next-non-holiday rule these years.
    return None if dt.year in [2021] else weekend_to_monday(dt)


def unity_day_observance(dt: datetime.datetime) -> datetime.datetime | None:
    # Unity Day did not follow the next-non-holiday rule these years.
    return None if dt.year in [2023] else weekend_to_monday(dt)


NewYearsDay = new_years_day(observance=new_years_day_observance)
NewYearsHoliday = Holiday(
    "New Year's Holiday",
    month=1,
    day=2,
    observance=new_years_holiday_observance,
)
NewYearsHoliday2 = Holiday(
    "New Year's Holiday",
    month=1,
    day=3,
    start_date="2005",
    end_date="2012",
)
NewYearsHoliday3 = Holiday(
    "New Year's Holiday",
    month=1,
    day=4,
    start_date="2005",
    end_date="2012",
)
NewYearsHoliday4 = Holiday(
    "New Year's Holiday",
    month=1,
    day=5,
    start_date="2005",
    end_date="2012",
)
NewYearsHoliday5 = Holiday(
    "New Year's Holiday",
    month=1,
    day=6,
    start_date="2005",
    end_date="2012",
)

OrthodoxChristmas = Holiday(
    "Orthodox Christmas",
    month=1,
    day=7,
    observance=orthodox_christmas_observance,
)

DefenderOfTheFatherlandDay = Holiday(
    "Defender of the Fatherland Day",
    month=2,
    day=23,
    observance=defender_of_fatherland_observance,
)

WomensDay = Holiday(
    "Women's Day",
    month=3,
    day=8,
    observance=weekend_to_monday,
)

LabourDay = european_labour_day(observance=weekend_to_monday)

VictoryDay = Holiday(
    "Victory Day",
    month=5,
    day=9,
    observance=victory_day_observance,
)

DayOfRussia = Holiday(
    "Day of Russia",
    month=6,
    day=12,
    observance=day_of_russia_observance,
)

UnityDay = Holiday(
    "Unity Day",
    month=11,
    day=4,
    observance=unity_day_observance,
    start_date="2005",
)

NewYearsEve = new_years_eve(
    observance=new_years_eve_observance,
    days_of_week=WEEKDAYS,
)


# Adhoc Holidays
# --------------

# All of the following "extensions" are bridge holidays, meaning they are
# either a Monday or Friday that is made into a holiday to fill in the gap
# between a Tuesday or Thursday holiday, respectively. Unfortunately having
# these bridge days is not consistently the rule, so they are treated as adhoc.
# This means that in the future there may be manual additions needed here.
new_years_extensions = [
    "2003-01-03",
    "2013-01-03",
    "2013-01-04",
    "2014-01-03",
]

orthodox_christmas_extensions = [
    "2003-01-06",
    "2005-01-10",
    "2008-01-08",
    "2009-01-08",
    "2009-01-09",
    "2010-01-08",
    "2011-01-10",
    "2016-01-08",
]

defender_of_the_fatherland_extensions = [
    "2006-02-24",
    "2010-02-22",
]

womens_day_extensions = [
    "2005-03-07",
    "2011-03-07",
    "2012-03-09",
    "2022-03-07",
]

labour_day_extensions = [
    "2002-05-02",
    "2002-05-03",
    "2003-05-02",
    "2004-05-04",
    "2007-04-30",
    "2008-05-02",
    "2012-04-30",
    "2015-05-04",
    "2016-05-03",
    # LabourDay Holiday extended to Tuesday.
    "2022-05-03",
]

victory_day_extensions = [
    "2002-05-10",
    "2005-05-10",
    "2006-05-08",
    "2017-05-08",
    # Victory Day Holiday extended to Tuesday.
    "2022-05-10",
]

day_of_russia_extensions = [
    "2003-06-13",
    "2007-06-11",
    "2008-06-13",
    "2012-06-11",
    "2014-06-13",
]

unity_day_extensions = [
    "2008-11-03",
    "2010-11-05",
]

misc_adhoc = [
    # Exchange Holidays.
    "2002-11-07",
    "2002-11-08",
    "2002-12-12",
    "2002-12-13",
    "2003-11-07",
    "2003-12-12",
    "2004-11-08",
    "2004-12-13",
    "2008-09-18",
    # Trading Suspended.
    "2008-10-10",
    "2008-10-27",
    # Non-Working Days.
    "2020-06-24",
    "2020-07-01",
]


class XMOSExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Moscow Stock Exchange.

    Open Time: 10:00 AM, MSK (Moscow Standard Time)
    Close Time: 6:45 PM, MSK (Moscow Standard Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - New Year's Holiday
      - Orthodox Christmas Day
      - Defender of the Fatherland Day
      - Women's Day
      - Spring and Labour Day
      - Victory Day
      - Day of Russia
      - Unity Day
      - New Year's Eve

    Holidays No Longer Observed:
      - New Year's Holiday Week

    Early Closes:
      - None
    """

    name = "XMOS"

    tz = ZoneInfo("Europe/Moscow")

    open_times = ((None, datetime.time(10)),)

    close_times = ((None, datetime.time(18, 45)),)

    @property
    def special_weekmasks(self):
        """
        Returns
        -------
        list: List of (date, date, str) tuples that represent special
         weekmasks that applies between dates.
        """
        return [
            # For 1999-2011 years next url was used to obtain data for
            # IMOEX close values in order to check if there are any Sat or Sun:
            # https://iss.moex.com/iss/history/engines/stock/markets/index/securities/IMOEX
            (pd.Timestamp("1999-01-04"), pd.Timestamp("1999-01-10"), "1111101"),
            (pd.Timestamp("2000-05-01"), pd.Timestamp("2000-05-07"), "1111110"),
            (pd.Timestamp("2000-10-30"), pd.Timestamp("2000-11-05"), "1111110"),
            (pd.Timestamp("2000-12-04"), pd.Timestamp("2000-12-10"), "1111110"),
            (pd.Timestamp("2001-03-05"), pd.Timestamp("2001-03-11"), "1111101"),
            (pd.Timestamp("2001-04-23"), pd.Timestamp("2001-04-29"), "1111110"),
            (pd.Timestamp("2001-06-04"), pd.Timestamp("2001-06-10"), "1111110"),
            (pd.Timestamp("2001-12-24"), pd.Timestamp("2001-12-30"), "1111110"),
            (pd.Timestamp("2002-04-22"), pd.Timestamp("2002-04-28"), "1111110"),
            (pd.Timestamp("2002-05-13"), pd.Timestamp("2002-05-19"), "1111110"),
            (pd.Timestamp("2002-11-04"), pd.Timestamp("2002-11-10"), "1111101"),
            (pd.Timestamp("2002-12-09"), pd.Timestamp("2002-12-15"), "1111101"),
            (pd.Timestamp("2002-12-30"), pd.Timestamp("2003-01-05"), "1111111"),
            (pd.Timestamp("2003-06-16"), pd.Timestamp("2003-06-22"), "1111110"),
            (pd.Timestamp("2005-02-28"), pd.Timestamp("2005-03-06"), "1111110"),
            (pd.Timestamp("2005-05-09"), pd.Timestamp("2005-05-15"), "1111110"),
            (pd.Timestamp("2006-02-20"), pd.Timestamp("2006-02-26"), "1111101"),
            (pd.Timestamp("2006-05-01"), pd.Timestamp("2006-05-07"), "1111110"),
            (pd.Timestamp("2007-04-23"), pd.Timestamp("2007-04-29"), "1111110"),
            (pd.Timestamp("2007-06-04"), pd.Timestamp("2007-06-10"), "1111110"),
            (pd.Timestamp("2008-04-28"), pd.Timestamp("2008-05-04"), "1111101"),
            (pd.Timestamp("2008-06-02"), pd.Timestamp("2008-06-08"), "1111110"),
            (pd.Timestamp("2008-10-27"), pd.Timestamp("2008-11-02"), "1111110"),
            (pd.Timestamp("2009-01-05"), pd.Timestamp("2009-01-11"), "1111101"),
            (pd.Timestamp("2010-02-22"), pd.Timestamp("2010-02-28"), "1111110"),
            (pd.Timestamp("2010-11-08"), pd.Timestamp("2010-11-14"), "1111110"),
            (pd.Timestamp("2011-02-28"), pd.Timestamp("2011-03-06"), "1111110"),
            # For 2012 year https://www.moex.com/a254
            (pd.Timestamp("2012-03-05"), pd.Timestamp("2012-03-11"), "1111101"),
            (pd.Timestamp("2012-04-23"), pd.Timestamp("2012-05-13"), "1111110"),
            (pd.Timestamp("2012-06-04"), pd.Timestamp("2012-06-10"), "1111110"),
            # For 2016 year https://www.moex.com/a3367
            (pd.Timestamp("2016-02-15"), pd.Timestamp("2016-02-21"), "1111110"),
            # For 2018 year https://www.moex.com/a4187
            (pd.Timestamp("2018-04-23"), pd.Timestamp("2018-04-29"), "1111110"),
            (pd.Timestamp("2018-06-04"), pd.Timestamp("2018-06-10"), "1111110"),
            (pd.Timestamp("2018-12-24"), pd.Timestamp("2018-12-30"), "1111110"),
            # For 2021 year https://www.moex.com/n30445
            (pd.Timestamp("2021-02-15"), pd.Timestamp("2021-02-21"), "1111110"),
            # For 2024 year https://www.moex.com/n64121
            (pd.Timestamp("2024-04-22"), pd.Timestamp("2024-04-28"), "1111110"),
            (pd.Timestamp("2024-10-28"), pd.Timestamp("2024-11-03"), "1111110"),
            (pd.Timestamp("2024-12-23"), pd.Timestamp("2024-12-29"), "1111110"),
        ]

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                NewYearsHoliday,
                NewYearsHoliday2,
                NewYearsHoliday3,
                NewYearsHoliday4,
                NewYearsHoliday5,
                OrthodoxChristmas,
                DefenderOfTheFatherlandDay,
                WomensDay,
                LabourDay,
                VictoryDay,
                DayOfRussia,
                UnityDay,
                NewYearsEve,
            ]
        )

    @property
    def adhoc_holidays(self):
        return list(
            chain(
                new_years_extensions,
                orthodox_christmas_extensions,
                defender_of_the_fatherland_extensions,
                womens_day_extensions,
                labour_day_extensions,
                victory_day_extensions,
                day_of_russia_extensions,
                unity_day_extensions,
                misc_adhoc,
            ),
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
