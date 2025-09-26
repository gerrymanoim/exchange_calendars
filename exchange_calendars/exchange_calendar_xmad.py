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

from pandas.tseries.holiday import EasterMonday, GoodFriday, Holiday, weekend_to_monday

from .common_holidays import (
    all_saints_day,
    assumption_day,
    boxing_day,
    christmas,
    christmas_eve,
    epiphany,
    european_labour_day,
    immaculate_conception,
    new_years_day,
    new_years_eve,
)
from .exchange_calendar import WEEKDAYS, HolidayCalendar, ExchangeCalendar

NewYearsDay = new_years_day()

Epiphany = epiphany(end_date="2007")

LabourDay = european_labour_day()

AssumptionDay = assumption_day(end_date="2005", observance=weekend_to_monday)

NationalDay = Holiday(
    "National Day",
    month=10,
    day=12,
    end_date="2005",
)

AllSaintsDay = all_saints_day(end_date="2005")

ConstitutionDay = Holiday(
    "Constitution Day",
    month=12,
    day=6,
    end_date="2005",
)

ImmaculateConception = immaculate_conception(end_date="2005")

ChristmasEveThrough2010 = christmas_eve(end_date="2011")
ChristmasEve2021to2023 = christmas_eve(
    start_date="2021",
    end_date="2024",
)
ChristmasEveEarlyClose2012To2020 = christmas_eve(
    start_date="2012",
    end_date="2021",
    days_of_week=(WEEKDAYS),
)
ChristmasEveEarlyCloseFrom2024 = christmas_eve(
    start_date="2024",
    days_of_week=(WEEKDAYS),
)
Christmas = christmas()
BoxingDay = boxing_day()

NewYearsEveThrough2010 = new_years_eve(end_date="2011")
NewYearsEve2021to2023 = new_years_eve(start_date="2021", end_date="2024")
NewYearsEveEarlyClose2012To2020 = new_years_eve(
    start_date="2012",
    end_date="2021",
    days_of_week=(WEEKDAYS),
)
NewYearsEveEarlyCloseFrom2024 = new_years_eve(
    start_date="2024",
    days_of_week=(WEEKDAYS),
)


class XMADExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Madrid Stock Exchange (Bolsa de Madrid).
    https://www.bolsasymercados.es/bme-exchange/en/Trading/Trading-Calendar

    Open Time: 9:00 AM, CET (Central European Time)
    Close Time: 5:30 PM, CET (Central European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Good Friday
      - Easter Monday
      - Labour Day
      - Christmas Eve (apart from when it was observed as an early close)
      - Christmas Day
      - Boxing Day

    Holidays No Longer Observed:
      - Epiphany (until 2006, inclusive)
      - Assumption Day (until 2004, inclusive)
      - National Day (until 2004, inclusive)
      - All Saints Day (until 2004, inclusive)
      - Constitution Day (until 2004, inclusive)
      - Immaculate Conception (until 2004, inclusive)
      - New Year's Eve (until 2010, inclusive)

    Early Closes:
      - Christmas Eve (2012 to 2020, inclusive and from 2024)
      - New Year's Eve (2012 to 2020 inclusive and from 2024)
    """

    regular_early_close = time(14, 00)

    name = "XMAD"

    tz = ZoneInfo("Europe/Madrid")

    open_times = ((None, time(9)),)

    close_times = ((None, time(17, 30)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                Epiphany,
                GoodFriday,
                EasterMonday,
                LabourDay,
                AssumptionDay,
                NationalDay,
                AllSaintsDay,
                ConstitutionDay,
                ImmaculateConception,
                ChristmasEveThrough2010,
                ChristmasEve2021to2023,
                Christmas,
                BoxingDay,
                NewYearsEveThrough2010,
                NewYearsEve2021to2023,
            ]
        )

    @property
    def special_closes(self):
        return [
            (
                self.regular_early_close,
                HolidayCalendar(
                    [
                        ChristmasEveEarlyClose2012To2020,
                        ChristmasEveEarlyCloseFrom2024,
                        NewYearsEveEarlyClose2012To2020,
                        NewYearsEveEarlyCloseFrom2024,
                    ]
                ),
            )
        ]
