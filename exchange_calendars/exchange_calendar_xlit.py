from datetime import time
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import EasterMonday, GoodFriday, Holiday

from .common_holidays import (
    all_saints_day,
    ascension_day,
    assumption_day,
    boxing_day,
    christmas_eve,
    european_labour_day,
    new_years_day,
    new_years_eve,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

NewYearsDay = new_years_day()
LabourDay = european_labour_day()
AscensionDay = ascension_day()
AssumptionDay = assumption_day()
AllSaintsDay = all_saints_day()
ChristmasEve = christmas_eve()
BoxingDay = boxing_day()
NewYearsEve = new_years_eve()

RestorationOfTheState = Holiday("Restoration of the State", month=2, day=16)
RestorationOfIndependence = Holiday("Restoration of Independence", month=3, day=11)
StJohnsDay = Holiday("St. John's Day", month=6, day=24)
StatehoodDay = Holiday("Statehood Day", month=7, day=6)
AllSoulsDay = Holiday("All Souls' Day", month=11, day=2)


class XLITExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Vilnius Stock Exchange in Lithuania.
    https://nasdaqbaltic.com/statistics/en/calendar?holidays=1

    Open Time: 10:00 AM, EET (Eastern European Time)
    Close Time: 4:00 PM, EET (Eastern European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Restoration of the State (Feb 16)
      - Restoration of Independence (Mar 11)
      - Good Friday
      - Easter Monday
      - Labour Day (May 1)
      - Ascension Day
      - St. John's Day (Jun 24)
      - Statehood Day (Jul 6)
      - Assumption Day (Aug 15)
      - All Saints' Day (Nov 1)
      - All Souls' Day (Nov 2)
      - Christmas Eve (Dec 24)
      - Boxing Day (Dec 26)
      - New Year's Eve (Dec 31)
    """

    name = "XLIT"
    tz = ZoneInfo("Europe/Vilnius")
    open_times = ((None, time(10, 0)),)
    close_times = ((None, time(16, 0)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                RestorationOfTheState,
                RestorationOfIndependence,
                GoodFriday,
                EasterMonday,
                LabourDay,
                AscensionDay,
                StJohnsDay,
                StatehoodDay,
                AssumptionDay,
                AllSaintsDay,
                AllSoulsDay,
                ChristmasEve,
                BoxingDay,
                NewYearsEve,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [
            pd.Timestamp("2023-12-25"),  # Additional Day off
        ]
