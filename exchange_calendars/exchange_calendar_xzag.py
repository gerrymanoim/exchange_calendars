from datetime import time
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import (
    Holiday,
    EasterMonday,
    GoodFriday,
)

from .common_holidays import (
    new_years_day,
    epiphany,
    european_labour_day,
    corpus_christi,
    assumption_day,
    all_saints_day,
    christmas_eve,
    christmas,
    new_years_eve,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

NewYearsDay = new_years_day()
Epiphany = epiphany()
LabourDay = european_labour_day()
NationalDayFrom2020 = Holiday("National Day", month=5, day=30, start_date="2020")
NationalDayFrom2002To2020 = Holiday(
    "National Day", month=6, day=25, start_date="2002", end_date="2020"
)
NationalDayFrom1996To2002 = Holiday(
    "National Day", month=5, day=30, start_date="1996", end_date="2002"
)
CorpusChristi = corpus_christi(start_date="2002")
AntiFascistStruggleDay = Holiday("Anti-Fascist Struggle Day", month=6, day=22)
VictoryDay = Holiday("Victory and Homeland Thanksgiving Day", month=8, day=5)
AssumptionDay = assumption_day()
IndependenceDay = Holiday(
    "Independence Day", month=10, day=8, start_date="2002", end_date="2020"
)
AllSaintsDay = all_saints_day()
RemembranceDay = Holiday("Remembrance Day", month=11, day=18, start_date="2020")
ChristmasEve = christmas_eve()
Christmas = christmas()
StStephensDay = Holiday("St. Stephen's Day", month=12, day=26)
NewYearsEve = new_years_eve()


class XZAGExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Zagreb Stock Exchange (Croatia).
    https://zse.hr/en/non-trading-days/110

    Open Time: 9:00 AM
    Close Time: 4:00 PM

    Regularly-Observed Holidays:
      - New Year's Day (Jan 1)
      - Epiphany (Jan 6)
      - Good Friday
      - Easter Monday
      - Labour Day (May 1)
      - National Day (May 30)
      - Corpus Christi (movable, 60 days after Easter)
      - Anti-Fascist Struggle Day (Jun 22)
      - Victory and Homeland Thanksgiving Day (Aug 5)
      - Assumption Day (Aug 15)
      - All Saints' Day (Nov 1)
      - Remembrance Day (Nov 18)
      - Christmas Eve (Dec 24)
      - Christmas Day (Dec 25)
      - St. Stephen's Day (Dec 26)
      - New Year's Eve (Dec 31)
    """

    name = "XZAG"
    tz = ZoneInfo("Europe/Zagreb")
    open_times = ((None, time(9, 0)),)
    close_times = ((None, time(16, 0)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                Epiphany,
                GoodFriday,
                EasterMonday,
                LabourDay,
                NationalDayFrom2020,
                NationalDayFrom2002To2020,
                NationalDayFrom1996To2002,
                CorpusChristi,
                AntiFascistStruggleDay,
                VictoryDay,
                AssumptionDay,
                IndependenceDay,
                AllSaintsDay,
                RemembranceDay,
                ChristmasEve,
                Christmas,
                StStephensDay,
                NewYearsEve,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [
            pd.Timestamp("2024-04-17"),  # Election Day
            pd.Timestamp("2022-12-30"),  # Conversion of HRK to EUR
            pd.Timestamp("2022-12-29"),  # Conversion of HRK to EUR
        ]
