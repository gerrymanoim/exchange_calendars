from datetime import time
from zoneinfo import ZoneInfo

from pandas.tseries.holiday import (
    MO,
    DateOffset,
    EasterMonday,
    GoodFriday,
    Holiday,
    weekend_to_monday,
)

from .common_holidays import (
    boxing_day,
    christmas,
    new_years_day,
    weekend_boxing_day,
    weekend_christmas,
)
from .exchange_calendar import ExchangeCalendar, HolidayCalendar


NewYearsDay = new_years_day(observance=weekend_to_monday)

EarlyMayBankHoliday = Holiday(
    "Early May Bank Holiday",
    month=5,
    day=1,
    offset=DateOffset(weekday=MO(1)),
)

SpringBankHoliday = Holiday(
    "Spring Bank Holiday",
    month=5,
    day=31,
    offset=DateOffset(weekday=MO(-1)),
)

SummerBankHoliday = Holiday(
    "Summer Bank Holiday",
    month=8,
    day=31,
    offset=DateOffset(weekday=MO(-1)),
)

Christmas = christmas()
WeekendChristmas = weekend_christmas()
BoxingDay = boxing_day()
WeekendBoxingDay = weekend_boxing_day()


class XLMEExchangeCalendar(ExchangeCalendar):
    """Exchange calendar for the London Metal Exchange (XLME).
    https://www.lme.com/trading/trading-venues/trading-times

    Open Time: 1:00 AM, Europe/London
    Close Time: 7:00 PM, Europe/London

    Regularly-Observed Holidays:
    - New Year's Day
    - Good Friday
    - Easter Monday
    - Early May Bank Holiday
    - Spring Bank Holiday
    - Summer Bank Holiday
    - Christmas Day
    - Boxing Day
    """

    name = "XLME"

    tz = ZoneInfo("Europe/London")

    open_times = ((None, time(1)),)

    close_times = ((None, time(19)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                EasterMonday,
                EarlyMayBankHoliday,
                SpringBankHoliday,
                SummerBankHoliday,
                Christmas,
                WeekendChristmas,
                BoxingDay,
                WeekendBoxingDay,
            ]
        )
