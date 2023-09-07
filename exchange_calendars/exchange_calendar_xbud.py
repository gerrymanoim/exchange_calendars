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
from zoneinfo import ZoneInfo

from pandas.tseries.holiday import Easter, EasterMonday, Holiday
from pandas.tseries.offsets import Day

from .common_holidays import (
    all_saints_day,
    christmas,
    christmas_eve,
    european_labour_day,
    new_years_day,
    new_years_eve,
    whit_monday,
)
from .exchange_calendar import THURSDAY, TUESDAY, HolidayCalendar, ExchangeCalendar


ONE_DAY = datetime.timedelta(1)


def bridge_mon(dt: datetime.datetime) -> datetime.datetime | None:
    """Define Monday as holiday if Tuesday is a holiday.

    If a holiday falls on a Tuesday an extra holiday is observed on Monday
    to bridge the weekend and the official holiday.
    """
    return dt - ONE_DAY if dt.weekday() == TUESDAY else None


def bridge_fri(dt: datetime.datetime) -> datetime.datetime | None:
    """Define Friday as holiday if Thrusday is a holiday.

    If a holiday falls on a Thursday an extra holiday is observed on Friday
    to bridge the weekend and the official holiday.
    """
    return dt + ONE_DAY if dt.weekday() == THURSDAY else None


NewYearsDayExtraMon = new_years_day(observance=bridge_mon)
NewYearsDayExtraFri = new_years_day(observance=bridge_fri)

NationalHoliday1 = Holiday("National Day", month=3, day=15)
NationalHoliday1ExtraMon = Holiday(
    "National Day extra Monday", month=3, day=15, observance=bridge_mon
)
NationalHoliday1ExtraFri = Holiday(
    "National Day extra Friday", month=3, day=15, observance=bridge_fri
)

# Need custom start year so can't use pandas GoodFriday
GoodFriday = Holiday(
    "Good Friday", month=1, day=1, offset=[Easter(), Day(-2)], start_date="2012"
)

LabourDayExtraMon = european_labour_day(observance=bridge_mon)
LabourDayExtraFri = european_labour_day(observance=bridge_fri)

WhitMonday = whit_monday()

StStephensDay = Holiday("St. Stephen's Day", month=8, day=20)
StStephensDayExtraMon = Holiday(
    "St. Stephen's Day extra Monday", month=8, day=20, observance=bridge_mon
)
StStephensDayExtraFri = Holiday(
    "St. Stephen's Day extra Friday", month=8, day=20, observance=bridge_fri
)

NationalHoliday2 = Holiday("National Day", month=10, day=23)
NationalHoliday2ExtraMon = Holiday(
    "National Day extra Monday", month=10, day=23, observance=bridge_mon
)
NationalHoliday2ExtraFri = Holiday(
    "National Day extra Friday", month=10, day=23, observance=bridge_fri
)

AllSaintsDayExtraMon = all_saints_day(observance=bridge_mon)
AllSaintsDayExtraFri = all_saints_day(observance=bridge_fri)

# Christmas Eve does not follow the four day weekend rule
ChristmasEve = christmas_eve()

ChristmasDay = christmas()

# XBUD always has a holiday for the second day of Christmas (26th),
# but starting in 2013 if the 26th falls on a Thursday then the
# 27th (Friday) is also taken off
SecondDayOfChristmas = Holiday("Second Day of Christmas", month=12, day=26)
SecondDayOfChristmasExtraFri = Holiday(
    "Second Day of Christmas extra Friday",
    month=12,
    day=26,
    start_date="2013",
    observance=bridge_fri,
)
# SecondDayOfChristmas unnecessary to bridge_mon as if second day of christmas
# is a tuesday then monday will already be a holiday (Chirstmas Day)


# Starting in 2011, New Year's Eve is observed as a holiday every year.
# In some cases pre-2011, the 31st becomes a holiday due to the four day
# weekend rule (when Jan 1 falls on a Tuesday).
# Also, when NYE starts being observed as a holiday it does NOT follow
# the four day weekend rule (no 30ths are holidays)
NewYearsEve = new_years_eve(start_date="2011")


class XBUDExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Budapest Stock Exchange (XBUD).

    Open Time: 9:00 AM, CET
    Close Time: 5:00 PM, CET

    Regularly-Observed Holidays:
    - New Year's Day
    - National Holiday (Mar 15)
    - Good Friday
    - Easter Monday
    - Labour Day (May 1)
    - Whit Monday (50 days after Easter Sunday)
    - St. Stephen's Day (Aug 20)
    - National Holiday (Oct 23)
    - All Saint's Day (Nov 1)
    - Christmas Eve
    - Christmas Day
    - Second Day of Christmas (Dec 26)
    - New Year's Eve

    Early Closes:
    - None
    """

    name = "XBUD"

    tz = ZoneInfo("Europe/Budapest")

    open_times = ((None, datetime.time(9)),)

    close_times = ((None, datetime.time(17, 00)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                new_years_day(),
                NewYearsDayExtraMon,
                NewYearsDayExtraFri,
                NationalHoliday1,
                NationalHoliday1ExtraMon,
                NationalHoliday1ExtraFri,
                GoodFriday,
                EasterMonday,
                european_labour_day(),
                LabourDayExtraMon,
                LabourDayExtraFri,
                WhitMonday,
                StStephensDay,
                StStephensDayExtraMon,
                StStephensDayExtraFri,
                NationalHoliday2,
                NationalHoliday2ExtraMon,
                NationalHoliday2ExtraFri,
                all_saints_day(),
                AllSaintsDayExtraMon,
                AllSaintsDayExtraFri,
                ChristmasEve,
                ChristmasDay,
                SecondDayOfChristmas,
                SecondDayOfChristmasExtraFri,
                NewYearsEve,
            ]
        )
