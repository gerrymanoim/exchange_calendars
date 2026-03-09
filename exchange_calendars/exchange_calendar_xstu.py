from datetime import time
from zoneinfo import ZoneInfo

from pandas.tseries.holiday import EasterMonday, GoodFriday
from .common_holidays import (
    boxing_day,
    christmas,
    christmas_eve,
    european_labour_day,
    new_years_day,
    new_years_eve,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

# Regular Holidays
# ----------------
NewYearsDay = new_years_day()

EuropeanLabourDay = european_labour_day()

ChristmasEve = christmas_eve()

Christmas = christmas()

BoxingDay = boxing_day()

NewYearsEve = new_years_eve()


class XSTUExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Börse Stuttgart (XSTU).
    https://www.boerse-stuttgart.de/en/investing/market-hours/

    Open Time: 7:30 AM, CET
    Close Time: 10:00 PM, CET

    Regularly-Observed Holidays:
    - New Years Day
    - Good Friday
    - Easter Monday
    - Labour Day
    - Christmas Eve
    - Christmas Day
    - Boxing Day
    - New Years Eve
    """

    name = "XSTU"

    tz = ZoneInfo("Europe/Berlin")

    open_times = ((None, time(7, 30)),)

    close_times = ((None, time(22)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                EasterMonday,
                EuropeanLabourDay,
                ChristmasEve,
                Christmas,
                BoxingDay,
                NewYearsEve,
            ]
        )
