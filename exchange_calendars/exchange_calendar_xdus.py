# LICENSE HERE

from datetime import time
from zoneinfo import ZoneInfo

from pandas import Timestamp
from pandas.tseries.holiday import EasterMonday, GoodFriday, Holiday, previous_workday

from .common_holidays import (
    boxing_day,
    christmas,
    christmas_eve,
    european_labour_day,
    new_years_day,
    new_years_eve,
    whit_monday,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

# Regular Holidays
# ----------------
NewYearsDay = new_years_day()

EuropeanLabourDay = european_labour_day()

# Whit Monday observed in 2007, before it became regularly observed
# starting in 2015.
WhitMonday2007AdHoc = Timestamp("2007-05-28")

# Whit Monday and the Day of German Unity have been observed regularly, but in 2022 regular trading took place instead.
#  It's unclear if it will be observed in 2023.
WhitMondayUntil2022 = whit_monday(start_date="2015-01-01", end_date="2022-01-01")

DayOfGermanUnityUntil2022 = Holiday(
    "Day of German Unity",
    month=10,
    day=3,
    start_date="2014-01-01",
    end_date="2022-01-01",
)

# Reformation Day was a German national holiday in 2017.
ReformationDay500thAnniversaryAdHoc = Timestamp("2017-10-31")

ChristmasEve = christmas_eve()

Christmas = christmas()

BoxingDay = boxing_day()

NewYearsEve = new_years_eve()

# Early Closes
# ------------
# The last weekday before Dec 31 is an early close starting in 2010.
LastWorkingDay = Holiday(
    "Last Working Day of Year Early Close",
    month=12,
    day=31,
    start_date="2010-01-01",
    observance=previous_workday,
)


class XDUSExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Dusseldorf Stock Exchange (XDUS).
    Compared to Frankfurt:
    - same holidays
    - earlier open, later close
    Identical to Hamburg

    Open Time: 8:00 AM, CET
    Close Time: 10:00 PM, CET

    Regularly-Observed Holidays:
    - New Years Day
    - Good Friday
    - Easter Monday
    - Whit Monday
    - Labour Day
    - Day of German Unity
    - Christmas Eve
    - Christmas Day
    - Boxing Day

    Early Closes:
    - Last working day before Dec. 31
    """

    # TODO: verify the early close time
    # Assume same as Frankfurt
    regular_early_close = time(14)

    name = "XDUS"

    tz = ZoneInfo("Europe/Brussels")

    open_times = ((None, time(8)),)

    close_times = ((None, time(22)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                EasterMonday,
                EuropeanLabourDay,
                WhitMondayUntil2022,
                DayOfGermanUnityUntil2022,
                ChristmasEve,
                Christmas,
                BoxingDay,
                NewYearsEve,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [
            WhitMonday2007AdHoc,
            ReformationDay500thAnniversaryAdHoc,
        ]

    @property
    def special_closes(self):
        return [
            (
                self.regular_early_close,
                HolidayCalendar(
                    [
                        LastWorkingDay,
                    ]
                ),
            )
        ]
