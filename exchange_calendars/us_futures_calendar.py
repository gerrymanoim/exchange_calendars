from datetime import time

from pandas import Timedelta, Timestamp
from pandas.tseries.holiday import GoodFriday
from pytz import UTC, timezone

from .exchange_calendar import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar, end_default
from exchange_calendars.us_holidays import Christmas, USNewYearsDay

# Number of hours of offset between the open and close times dictated by this
# calendar versus the 6:31am to 5:00pm times over which we want to simulate
# futures algos.
FUTURES_OPEN_TIME_OFFSET = 12.5
FUTURES_CLOSE_TIME_OFFSET = -1


class QuantopianUSFuturesCalendar(ExchangeCalendar):
    """Synthetic calendar for trading US futures.

    This calendar is a superset of all of the US futures exchange
    calendars provided by Zipline (CFE, CME, ICE), and is intended for
    trading across all of these exchanges.

    Notes
    -----
    Open Time: 6:00 PM, America/New_York
    Close Time: 6:00 PM, America/New_York

    Regularly-Observed Holidays:
    - New Years Day
    - Good Friday
    - Christmas

    In order to align the hours of each session, we ignore the Sunday
    CME Pre-Open hour (5-6pm).
    """

    # XXX: Override the default ExchangeCalendar start and end dates with ones
    # further in the future. This is a stopgap for memory issues caused by
    # upgrading to pandas 18. This calendar is the most severely affected,
    # since it has the most total minutes of any of the zipline calendars.
    def __init__(self, start=Timestamp("2000-01-01", tz=UTC), end=end_default):
        super(QuantopianUSFuturesCalendar, self).__init__(start=start, end=end)

    name = "us_futures"
    tz = timezone("America/New_York")
    open_times = ((None, time(18, 1)),)
    close_times = ((None, time(18)),)
    open_offset = -1

    def execution_time_from_open(self, open_dates):
        return open_dates + Timedelta(hours=FUTURES_OPEN_TIME_OFFSET)

    def execution_time_from_close(self, close_dates):
        return close_dates + Timedelta(hours=FUTURES_CLOSE_TIME_OFFSET)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                USNewYearsDay,
                GoodFriday,
                Christmas,
            ]
        )
