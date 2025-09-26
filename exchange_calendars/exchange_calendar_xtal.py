from datetime import time
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import EasterMonday, GoodFriday, Holiday

from .common_holidays import (
    ascension_day,
    boxing_day,
    christmas_eve,
    new_years_day,
    new_years_eve,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

NewYearsDay = new_years_day()
AscensionDay = ascension_day()
ChristmasEve = christmas_eve()
BoxingDay = boxing_day()
NewYearsEve = new_years_eve()

IndependenceDay = Holiday("Independence Day", month=2, day=24)
SpringDay = Holiday("Spring Day", month=5, day=1)
VictoryDay = Holiday("Victory Day", month=6, day=23)
MidsummerDay = Holiday("Saint John's Day", month=6, day=24)
RestorationOfIndependence = Holiday("Independence Restoration Day", month=8, day=20)


class XTALExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Tallinn Stock Exchange (Estonia).
    https://nasdaqbaltic.com/statistics/en/calendar?holidays=1

    Open Time: 10:00 AM, EET (Eastern European Time)
    Close Time: 4:00 PM, EET (Eastern European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Independence Day (Feb 24)
      - Good Friday
      - Easter Monday
      - Spring Day (May 1)
      - Ascension Day
      - Victory Day (Jun 23)
      - Midsummer Day (Jun 24)
      - Restoration of Independence (Aug 20)
      - Christmas Eve (Dec 24)
      - Boxing Day (Dec 26)
      - New Year's Eve (Dec 31)
    """

    name = "XTAL"
    tz = ZoneInfo("Europe/Tallinn")
    open_times = ((None, time(10, 0)),)
    close_times = ((None, time(16, 0)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                IndependenceDay,
                GoodFriday,
                EasterMonday,
                SpringDay,
                AscensionDay,
                VictoryDay,
                MidsummerDay,
                RestorationOfIndependence,
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
