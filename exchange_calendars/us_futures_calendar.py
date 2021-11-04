from datetime import time

import numpy as np
import pandas as pd
from pandas.tseries.holiday import GoodFriday
from pytz import UTC, timezone

from exchange_calendars.exchange_calendar import ExchangeCalendar, HolidayCalendar
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

    name = "us_futures"
    tz = timezone("America/New_York")
    open_times = ((None, time(18)),)
    close_times = ((None, time(18)),)
    open_offset = -1

    def execution_time_from_open(self, open_dates):
        return open_dates + pd.Timedelta(hours=FUTURES_OPEN_TIME_OFFSET)

    def execution_time_from_close(self, close_dates):
        return close_dates + pd.Timedelta(hours=FUTURES_CLOSE_TIME_OFFSET)

    def execution_minutes_for_session(
        self, session_label: pd.DatetimeIndex
    ) -> pd.DatetimeIndex:
        """
        Given a session label, return the execution minutes for that session.

        Parameters
        ----------
        session_label
            A session label whose session's minutes are desired.

        Returns
        -------
        pd.DateTimeIndex
            All the execution minutes for the given session.
        """
        start = self.execution_time_from_open(self.session_first_minute(session_label))
        end = self.execution_time_from_close(self.session_last_minute(session_label))
        return self.minutes_in_range(start_minute=start, end_minute=end)

    def execution_minutes_for_sessions_in_range(self, start, stop):
        minutes = self.execution_minutes_for_session
        return pd.DatetimeIndex(
            np.concatenate(
                [minutes(session) for session in self.sessions_in_range(start, stop)]
            ),
            tz=UTC,
        )

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                USNewYearsDay,
                GoodFriday,
                Christmas,
            ]
        )
