from datetime import time
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import (
    Holiday,
    next_monday,
    EasterMonday,
    GoodFriday,
)

from .common_holidays import (
    ascension_day,
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
ChristmasEve = christmas_eve()
BoxingDay = boxing_day()
NewYearsEve = new_years_eve()

RestorationOfIndependence = Holiday(
    "Restoration of Independence", month=5, day=4, observance=next_monday
)

MidsummerEve = Holiday("Midsummer's Eve", month=6, day=23)

MidsummerDay = Holiday("Midsummer's Day", month=6, day=24)

ProclamationDay = Holiday("Proclamation Day", month=11, day=18, observance=next_monday)


class XRISExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Nasdaq Riga Stock Exchange (Latvia).
    https://nasdaqbaltic.com/statistics/en/calendar?holidays=1

    Open Time: 10:00 AM, EET (Eastern European Time)
    Close Time: 4:00 PM, EET (Eastern European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Good Friday
      - Easter Monday
      - Labour Day (May 1)
      - Restoration of Independence (May 4)
      - Ascension Day
      - Midsummer's Eve (Jun 23)
      -	Midsummer's Day (Jun 24)
      - Proclamation Day (Nov 18)
      - Christmas Eve (Dec 24)
      - Boxing Day (Dec 26)
      - New Year's Eve (Dec 31)
    """

    name = "XRIS"
    tz = ZoneInfo("Europe/Riga")
    open_times = ((None, time(10, 0)),)
    close_times = ((None, time(16, 0)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                EasterMonday,
                LabourDay,
                RestorationOfIndependence,
                AscensionDay,
                MidsummerEve,
                MidsummerDay,
                ProclamationDay,
                ChristmasEve,
                BoxingDay,
                NewYearsEve,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [
            pd.Timestamp(
                "2028-07-10"
            ),  # National Holiday - Latvian Song and Dance Festival (every 5 years)
            pd.Timestamp("2025-11-17"),  # Additional Day off - Latvia's National Day
            pd.Timestamp("2025-05-02"),  # Additional Day off
            pd.Timestamp(
                "2024-12-30"
            ),  # Additional Day off - Compensation by 28 December
            pd.Timestamp(
                "2024-12-23"
            ),  # Additional Day off - Compensation by 14 December
            pd.Timestamp("2023-12-25"),  # Additional Day off
            pd.Timestamp(
                "2023-07-10"
            ),  # National Holiday - Latvian Song and Dance Festival (every 5 years)
            pd.Timestamp(
                "2023-05-05"
            ),  # Additional Day off - Compensation by Saturday 20 May (bridge day)
            pd.Timestamp(
                "2018-05-09"
            ),  # National Holiday - Latvian Song and Dance Festival (every 5 years)
        ]
