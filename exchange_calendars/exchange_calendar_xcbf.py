from datetime import time
from itertools import chain
from zoneinfo import ZoneInfo

from pandas.tseries.holiday import (
    GoodFriday,
    USLaborDay,
    USPresidentsDay,
    USThanksgivingDay,
)

from .exchange_calendar import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.us_holidays import (
    Christmas,
    HurricaneSandyClosings,
    USBlackFridayInOrAfter1993,
    USIndependenceDay,
    USMartinLutherKingJrAfter1998,
    USMemorialDay,
    USNationalDaysofMourning,
    USNewYearsDay,
    USJuneteenth,
)


class XCBFExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the CBOE Futures Exchange (XCBF).

    http://cfe.cboe.com/aboutcfe/expirationcalendar.aspx

    Open Time: 8:30am, America/Chicago
    Close Time: 3:15pm, America/Chicago

    (We are ignoring extended trading hours for now)
    """

    name = "XCBF"

    tz = ZoneInfo("America/Chicago")

    open_times = ((None, time(8, 30)),)

    close_times = ((None, time(15, 15)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                USNewYearsDay,
                USMartinLutherKingJrAfter1998,
                USPresidentsDay,
                GoodFriday,
                USIndependenceDay,
                USMemorialDay,
                USJuneteenth,
                USLaborDay,
                USThanksgivingDay,
                Christmas,
            ]
        )

    @property
    def special_closes(self):
        return [
            (
                time(12, 15),
                HolidayCalendar(
                    [
                        USBlackFridayInOrAfter1993,
                    ]
                ),
            )
        ]

    @property
    def adhoc_holidays(self):
        return list(
            chain(
                HurricaneSandyClosings,
                USNationalDaysofMourning,
            )
        )
