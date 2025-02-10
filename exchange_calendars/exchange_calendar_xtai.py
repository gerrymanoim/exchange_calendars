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


import datetime
from functools import partial
from itertools import chain
from typing import Callable
from zoneinfo import ZoneInfo
import pandas as pd
from pandas.tseries.holiday import (
    Holiday,
    nearest_workday,
    next_monday,
    previous_friday,
)

from .common_holidays import european_labour_day, new_years_day
from .exchange_calendar import (
    FRIDAY,
    MONDAY,
    THURSDAY,
    TUESDAY,
    ExchangeCalendar,
    HolidayCalendar,
)
from .lunisolar_holidays import (
    chinese_lunar_new_year_dates,
    dragon_boat_festival_dates,
    mid_autumn_festival_dates,
    qingming_festival_dates,
)

ONE_DAY = datetime.timedelta(1)


def check_after_2013(dt: datetime.datetime) -> bool:
    """Query if a date has a year component later than 2013."""
    return dt.year > 2013


def check_between_2013_2024(dt: datetime.datetime) -> bool:
    """Query if a date has a year component from 2014 thr 2023."""
    return 2024 > dt.year > 2013


def before_chinese_new_year_offset(holidays):
    """Offset holidays that fall on a weekend to the previous friday.

    Can be used to offset holidays that fall before Chinese New Year.
    """
    return pd.to_datetime(holidays.map(lambda d: previous_friday(d)))


def chinese_new_year_offset(holidays):
    """Offset holidays that fall on a weekend to the next monday.

    Can be used to offset holidays that fall after Chinese New Year.
    """
    return pd.to_datetime(holidays.map(lambda d: next_monday(d)))


def evalute_tomb_sweeping_weekday_extra(dt: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Evaluate extra tomb sweeping holdiays.

    Evalutes extra holidays when tomb sweeping day falls on a weekday.

    Reference: Taiwan Implementation Measures for Memorial Days and Holidays 1.5.2.1
    https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0020033
    """
    dts = []
    for d in dt:
        if d.year > 2012 and d.month == 4 and d.day == 4:
            if datetime.datetime(d.year, 4, 4).weekday() == THURSDAY:
                dts.append(datetime.datetime(d.year, 4, 5))
            else:
                dts.append(datetime.datetime(d.year, 4, 3))
    return pd.to_datetime(dts)


def nearest_weekday_from_2014(dt: datetime.datetime) -> datetime.datetime:
    """Return nearest weekday to a date that's later than 2013.

    If date is earlier than 2014 then returns `dt` as is.
    """
    return dt if dt.year < 2014 else nearest_workday(dt)


def holidays_nearest_weekday_from_2014(
    holidays: pd.DatetimeIndex,
) -> pd.DatetimeIndex:
    """Map `holidays` to nearest weekdays.

    holidays that are weekdays map to themselves.
    holidays before 2014 map to themselves.
    """
    return pd.to_datetime([nearest_weekday_from_2014(d) for d in holidays])


def nearest_weekday_2014_thr_2023(dt: datetime.datetime) -> datetime.datetime:
    """Return nearest weekday to a date from 2014 thr 2023.

    If date is of another year then returns `dt` as received.
    """
    return nearest_workday(dt) if 2024 > dt.year > 2013 else dt


def manual_nearest_weekday_2014_thr_2023(holidays):
    """Map holidays from 2013 thr 2023 to nearest weekday.

    holidays that are weekdays map to themselves.
    holidays earlier than 2014 or later than 2024 map to themselves.

    Can be used to implement nearest weekday observance rule for Chinese
    lunar calendar holidays from 2013 through 2023.
    """
    return pd.to_datetime(holidays.map(lambda d: nearest_weekday_2014_thr_2023(d)))


def manual_extra_days_07_thr_2023(holidays):
    """Return holidays to make up a four day weekend.

    Can be used to implement the four day weekend rule observed for Chinese
    lunar calendar holidays from 2007 through 2023.
    """
    friday_extras = [
        d + ONE_DAY
        for d in holidays
        if d.weekday() == THURSDAY and 2024 > d.year > 2006
    ]

    monday_extras = [
        d - ONE_DAY for d in holidays if d.weekday() == TUESDAY and 2024 > d.year > 2006
    ]

    return pd.to_datetime(friday_extras + monday_extras)


def bridge_mon(
    dt: datetime.datetime, checker: Callable = check_after_2013
) -> datetime.datetime | None:
    """Return previous Monday if date is a Tueday, otherwise None.

    Parameters
    ----------
    dt
        Date to query.

    checker
        Callable to implement additional checks. Should take a single
        parameter as a datetime.datetime and return a bool. `bridge_mon`
        will return None if `checker` returns False when passed `dt`.

        By default will check year of `dt` is later than 2013.
    """
    dt -= ONE_DAY
    return dt if (dt.weekday() == MONDAY and checker(dt)) else None


def bridge_fri(
    dt: datetime.datetime, checker: Callable = check_after_2013
) -> datetime.datetime | None:
    """Return following Friday if a date is a Thursday, otherwise None.

    Parameters
    ----------
    dt
        Date to query.

    checker
        Callable to implement additional checks. Should take a single
        parameter as a datetime.datetime and return a bool. `bridge_fri`
        will return None if `checker` returns False when passed `dt`.

        By default will check year of `dt` is later than 2013.
    """
    dt += ONE_DAY
    return dt if (dt.weekday() == FRIDAY and checker(dt)) else None


NewYearsDay = new_years_day(observance=nearest_weekday_from_2014)
NewYearsDayExtraMon = new_years_day(observance=bridge_mon)
NewYearsDayExtraFri = new_years_day(observance=bridge_fri)

bridge_mon_2014_thr_2023 = partial(bridge_mon, checker=check_between_2013_2024)
bridge_fri_2014_thr_2023 = partial(bridge_fri, checker=check_between_2013_2024)


PeaceMemorialDay = Holiday(
    "Peace Memorial Day", month=2, day=28, observance=nearest_weekday_from_2014
)
PeaceMemorialDayExtraMon = Holiday(
    "Peace Memorial Day extra Monday",
    month=2,
    day=28,
    observance=bridge_mon_2014_thr_2023,
)
PeaceMemorialDayExtraFri = Holiday(
    "Peace Memorial Day extra Friday",
    month=2,
    day=28,
    observance=bridge_fri_2014_thr_2023,
)


WomenAndChildrensDay = Holiday(
    "Women and Children's Day",
    month=4,
    day=4,
    start_date="2011",
    observance=nearest_weekday_from_2014,
)
WomenAndChildrensDayExtraMon = Holiday(
    "Women and Children's Day extra Monday",
    month=4,
    day=4,
    start_date="2011",
    observance=bridge_mon_2014_thr_2023,
)
WomenAndChildrensDayExtraFri = Holiday(
    "Women and Children's Day extra Friday",
    month=4,
    day=4,
    start_date="2011",
    observance=bridge_fri_2014_thr_2023,
)


LabourDay = european_labour_day(observance=nearest_weekday_2014_thr_2023)

NationalDay = Holiday(
    "National Day of the Republic of China",
    month=10,
    day=10,
    observance=nearest_weekday_from_2014,
)
NationalDayExtraMon = Holiday(
    "National Day of the Republic of China extra Monday",
    month=10,
    day=10,
    observance=bridge_mon_2014_thr_2023,
)
NationalDayExtraFri = Holiday(
    "National Day of the Republic of China extra Friday",
    month=10,
    day=10,
    observance=bridge_fri_2014_thr_2023,
)


chinese_new_year = chinese_new_year_offset(chinese_lunar_new_year_dates)

chinese_new_years_eve = before_chinese_new_year_offset(
    chinese_new_year - ONE_DAY,
)

chinese_new_years_eve_2 = before_chinese_new_year_offset(
    chinese_new_years_eve - ONE_DAY,
)

chinese_new_year_2 = chinese_new_year_offset(
    chinese_new_year + ONE_DAY,
)

chinese_new_year_3 = chinese_new_year_offset(
    chinese_new_year_2 + ONE_DAY,
)

tomb_sweeping_day = manual_nearest_weekday_2014_thr_2023(qingming_festival_dates)
tomb_sweeping_day_weekday_extras = evalute_tomb_sweeping_weekday_extra(
    qingming_festival_dates
)
tomb_sweeping_day_weekend_extras = holidays_nearest_weekday_from_2014(
    qingming_festival_dates
)

dragon_boat_festival = manual_nearest_weekday_2014_thr_2023(dragon_boat_festival_dates)
dragon_boat_festival_weekday_extras = manual_extra_days_07_thr_2023(
    dragon_boat_festival
)
dragon_boat_festival_weekend_extras = holidays_nearest_weekday_from_2014(
    dragon_boat_festival_dates
)

mid_autumn_festival = manual_nearest_weekday_2014_thr_2023(
    mid_autumn_festival_dates,
)
mid_autumn_festival_weekday_extras = manual_extra_days_07_thr_2023(mid_autumn_festival)
mid_autumn_festival_weekend_extras = holidays_nearest_weekday_from_2014(
    mid_autumn_festival_dates
)

# Taiwan takes multiple days off before and after chinese new year,
# and sometimes it is unclear precisely which days will be holidays.
chinese_new_year_extras = pd.to_datetime(
    [
        "2002-02-07",
        "2002-02-15",
        "2003-01-29",
        "2004-01-19",
        "2005-02-04",
        "2006-02-02",
        "2007-02-22",
        "2007-02-23",
        "2008-02-04",
        "2009-01-29",
        "2009-01-30",
        "2010-02-18",
        "2010-02-19",
        "2011-01-31",
        "2012-01-26",
        "2012-01-27",
        "2013-02-14",
        "2013-02-15",
        "2014-01-28",
        "2015-02-16",
        "2016-02-11",
        "2016-02-12",
        "2017-01-25",
        "2018-02-13",
        "2019-01-31",
        "2019-02-08",
        "2020-01-21",
        "2020-01-22",
        "2021-02-08",
        "2021-02-09",
        "2022-01-27",
        "2023-01-26",
        "2023-01-27",
        "2024-02-06",
        "2024-02-07",
        "2025-01-23",
        "2025-01-24",
    ]
)

# Some abnormal observances of regularly observed holidays.
extra_holidays = pd.to_datetime(
    [
        "2021-04-02",  # Women And Childrens Day
        "2020-04-02",  # Tomb Sweeping Day
        "2016-04-05",  # Tomb Sweeping Day
        "2012-12-31",  # New Year's Eve
        "2012-02-27",  # Peace Memorial Day
        "2009-01-02",  # New Year's Day
        "2006-10-09",  # National Day
        "2005-09-01",  # Bank Holiday
        "2018-04-06",  # Tomb Sweeping Day, https://www.dgpa.gov.tw/information?uid=41&pid=7488
        "2007-04-06",  # Tomb Sweeping Day
    ]
)

typhoons = pd.to_datetime(
    [
        "2024-10-03",
        "2024-10-02",
        "2024-07-25",
        "2024-07-24",
        "2023-08-03",
        "2019-09-30",
        "2019-08-09",
        "2016-09-28",
        "2016-09-27",
        "2016-07-08",
        "2015-09-29",
        "2015-07-10",
        "2014-07-23",
        "2013-08-21",
        "2012-08-02",
        "2009-08-07",
        "2008-09-29",
        "2008-07-28",
        "2007-09-18",
        "2005-08-05",
        "2005-07-18",
        "2004-10-25",
        "2004-08-25",
        "2004-08-24",
        "2002-09-06",
    ]
)


class XTAIExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Taiwan Stock Exchange Corporation (XTAI).
    https://www.twse.com.tw/en/trading/holiday.html

    Open Time: 9:00 AM, CST
    Close Time: 1:30 PM, CST

    Regularly-Observed Holidays:
    - New Year's Day
    - Chinese New Year's Eve
    - Chinese New Year
    - Peace Memorial Day (Feb 28)
    - Women and Children's Day (Apr 4)
    - Tomb Sweeping Day (Lunar Calendar)
    - Labour Day (May 1)
    - Dragon Boat Festival (Lunar Calendar)
    - Mid-Autumn Festival (Lunar Calendar)
    - National Day of the Republic of China (Oct 10)


    Early Closes:
    - None
    """

    name = "XTAI"

    tz = ZoneInfo("Asia/Taipei")

    open_times = ((None, datetime.time(9)),)

    close_times = ((None, datetime.time(13, 30)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                NewYearsDayExtraMon,
                NewYearsDayExtraFri,
                PeaceMemorialDay,
                PeaceMemorialDayExtraMon,
                PeaceMemorialDayExtraFri,
                WomenAndChildrensDay,
                WomenAndChildrensDayExtraMon,
                WomenAndChildrensDayExtraFri,
                LabourDay,
                NationalDay,
                NationalDayExtraMon,
                NationalDayExtraFri,
            ]
        )

    @property
    def adhoc_holidays(self):
        return list(
            chain(
                extra_holidays,
                typhoons,
                chinese_new_years_eve,
                chinese_new_years_eve_2,
                chinese_new_year,
                chinese_new_year_2,
                chinese_new_year_3,
                chinese_new_year_extras,
                tomb_sweeping_day,
                tomb_sweeping_day_weekday_extras,
                tomb_sweeping_day_weekend_extras,
                dragon_boat_festival,
                dragon_boat_festival_weekday_extras,
                dragon_boat_festival_weekend_extras,
                mid_autumn_festival,
                mid_autumn_festival_weekday_extras,
                mid_autumn_festival_weekend_extras,
            )
        )
