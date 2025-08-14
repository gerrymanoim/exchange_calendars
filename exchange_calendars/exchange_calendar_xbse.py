from datetime import time
from zoneinfo import ZoneInfo

from pandas.tseries.holiday import Holiday
from pandas.tseries.offsets import Day

from .common_holidays import (
    christmas,
    orthodox_good_friday,
    orthodox_easter_monday,
    european_labour_day,
    orthodox_pentecost,
    new_years_day,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar
from .pandas_extensions.offsets import OrthodoxEaster

NewYearsDay = new_years_day()

DayAfterNewYearsDay = Holiday("Day After New Year's Day", month=1, day=2)

RomanianPrincipalitiesUnificationDay = Holiday(
    "Romanian Principalities Unification Day", month=1, day=24
)

OrthodoxGoodFriday = orthodox_good_friday()

OrthodoxEasterMonday = orthodox_easter_monday()

LabourDay = european_labour_day()


ChildrensDay = Holiday(
    "Children's Day",
    month=6,
    day=1,
)

OrthodoxPentecost = orthodox_pentecost()

DescentOfTheHolySpirit = Holiday(
    "Descent of the Holy Spirit",
    month=1,
    day=1,
    offset=[OrthodoxEaster(), Day(50)],
)

StMarysDay = Holiday(
    "St. Mary's day",
    month=8,
    day=15,
)

StAndrewsDay = Holiday(
    "St. Andrew's day",
    month=11,
    day=30,
)

NationalDay = Holiday(
    "National Day",
    month=12,
    day=1,
)

ChristmasDay = christmas()

SecondDayOfChristmas = Holiday(
    "Second Day of Christmas",
    month=12,
    day=26,
)


class XBSEExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Bucharest Stock Exchange (XBSE).

    Open Time: 10:00 AM, EET
    Close Time: 5:45 PM, EET

    Regularly-Observed Holidays:
      - New Year's Day
      - Day after New Year's Day
      - Romanian Principalities Unification Day
      - Orthodox Good Friday
      - Orthodox Easter Monday
      - Labour Day
      - Orthodox Pentecost
      - Descent of the Holy Spirit
      - Children's Day
      - Assumption of Virgin Mary
      - St Andrew's day
      - Christmas
      - Day after Christmas

    Early Closes:
      - None
    """

    name = "XBSE"

    tz = ZoneInfo("Europe/Bucharest")

    open_times = ((None, time(10)),)

    close_times = ((None, time(17, 45)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                DayAfterNewYearsDay,
                RomanianPrincipalitiesUnificationDay,
                OrthodoxGoodFriday,
                OrthodoxEasterMonday,
                LabourDay,
                OrthodoxPentecost,
                DescentOfTheHolySpirit,
                ChildrensDay,
                StMarysDay,
                StAndrewsDay,
                NationalDay,
                ChristmasDay,
                SecondDayOfChristmas,
            ]
        )
