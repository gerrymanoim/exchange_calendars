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

NewYearsDay = new_years_day()
LabourDay = european_labour_day()
ChristmasEve = christmas_eve()
Christmas = christmas()
BoxingDay = boxing_day()
NewYearsEve = new_years_eve()


class XEEEExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the European Energy Exchange AG, Leipzig, Germany.
    https://www.eex.com/fileadmin/EEX/Downloads/Trading/Calendar/Holiday_Calendar/20230303_Trading_Calendar_EEX_Group.pdf

    Open Time: 8:00 AM, CET (Central European Time)
    Close Time: 6:00 PM, CET (Central European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Good Friday
      - Easter Monday
      - Labour Day
      - Christmas Eve
      - Christmas Day
      - Boxing Day
      - New Year's Eve
    """

    name = "XEEE"

    tz = ZoneInfo("Europe/Berlin")

    open_times = ((None, time(8)),)

    close_times = ((None, time(18, 0)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                EasterMonday,
                LabourDay,
                ChristmasEve,
                Christmas,
                BoxingDay,
                NewYearsEve,
            ]
        )
