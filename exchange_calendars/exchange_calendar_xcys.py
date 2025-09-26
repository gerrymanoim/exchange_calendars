from datetime import time
from zoneinfo import ZoneInfo
from .pandas_extensions.offsets import OrthodoxEaster
from pandas.tseries.holiday import (
    Holiday,
    EasterMonday,
    GoodFriday,
)
from pandas.tseries.offsets import Day
from .common_holidays import (
    new_years_day,
    epiphany,
    orthodox_good_friday,
    orthodox_easter_monday,
    orthodox_easter_tuesday,
    european_labour_day,
    assumption_day,
    christmas_eve,
    christmas,
    boxing_day,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

NewYearsDay = new_years_day()
Epiphany = epiphany()
GreekIndependenceDay = Holiday("Greek Independence Day", month=3, day=25)
GreenMonday = Holiday(
    "Green Monday", month=1, day=1, offset=[OrthodoxEaster(), -Day(48)]
)
CyprusNationalDay = Holiday("Cyprus National Day", month=4, day=1)
OrthodoxGoodFriday = orthodox_good_friday()
OrthodoxEasterMonday = orthodox_easter_monday()
OrthodoxEasterTuesday = orthodox_easter_tuesday()
LabourDay = european_labour_day()
HolySpiritDay = Holiday(
    "Holy Spirit Day", month=1, day=1, offset=[OrthodoxEaster(), Day(50)]
)
AssumptionDay = assumption_day()
CyprusIndependenceDay = Holiday("Cyprus Independence Day", month=10, day=1)
OkhiDay = Holiday("Okhi Day", month=10, day=28)
ChristmasEve = christmas_eve()
Christmas = christmas()
BoxingDay = boxing_day()


class XCYSExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Cyprus Stock Exchange.
    https://www.cse.com.cy/en-GB/regulated-market/market-indices/other-information/Public-Holiday/

    Open Time: 10:30 AM EET (Eastern European Time)
    Close Time: 5:00 PM EET (Eastern European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Epiphany (Jan 6)
      - Green Monday (Orthodox)
      - Cyprus National Day (Apr 1)
      - Greek Independence Day (Mar 25)
      - Good Friday (Catholic)
      - Easter Monday (Catholic)
      - Good Friday (Orthodox)
      - Easter Monday (Orthodox)
      - Easter Tuesday (Orthodox)
      - Labour Day (May 1)
      - Holy Spirit Day (Orthodox)
      - Assumption Day (Aug 15)
      - Cyprus Independence Day (Oct 1)
      - Okhi Day (Oct 28)
      - Christmas Eve (Dec 24)
      - Christmas Day (Dec 25)
      - Boxing Day (Dec 26)
    """

    name = "XCYS"
    tz = ZoneInfo("Asia/Nicosia")
    open_times = ((None, time(10, 30)),)
    close_times = ((None, time(17, 00)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                Epiphany,
                GreenMonday,
                CyprusNationalDay,
                GreekIndependenceDay,
                GoodFriday,
                EasterMonday,
                OrthodoxGoodFriday,
                OrthodoxEasterMonday,
                OrthodoxEasterTuesday,
                LabourDay,
                HolySpiritDay,
                AssumptionDay,
                CyprusIndependenceDay,
                OkhiDay,
                ChristmasEve,
                Christmas,
                BoxingDay,
            ]
        )

    @property
    def adhoc_holidays(self):
        return []
