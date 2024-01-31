import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xnys import XNYSExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXNYSCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XNYSExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2012
            "2012-01-02",
            "2012-01-16",
            "2012-02-20",
            "2012-04-06",
            "2012-05-28",
            "2012-07-04",
            "2012-09-03",
            "2012-11-22",
            "2012-12-25",
            #
            # Thanksgiving. Fourth Thursday of November
            "2005-11-24",  # November has 4 Thursdays
            "2006-11-23",  # November has 5 Thursdays
            # Holidays falling on a weekend and subsequently made up on Monday.
            "2012-01-02",  # New Year's Day fell on Sunday.
            # Juneteenth 2022-2024
            "2022-06-20",
            "2023-06-19",
            "2024-06-19",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        # NOTE: any date that is earlier than the first date of xnys.csv will NOT be
        # tested!
        yield [
            "2001-09-11",  # 9/11
            "2001-09-12",  # 9/11
            "2001-09-13",  # 9/11
            "2001-09-14",  # 9/11
            "2012-10-29",  # Hurricane Sandy
            "2012-10-30",  # Hurricane Sandy
            "1985-09-27",  # Hurricane Gloria
            "1977-07-14",  # New York Blackout
            "1972-11-07",  # pre-1980 Presidential Election Days
            "1976-11-02",  # pre-1980 Presidential Election Days
            "1980-11-04",  # pre-1980 Presidential Election Days
            "2018-12-05",  # George H.W. - 12/5/2018
            "2007-01-02",  # Gerald Ford
            "2004-06-11",  # Ronald Reagan
            "1994-04-27",  # Richard Nixon
            "1973-01-25",  # Lyndon B. Johnson
            "1972-12-28",  # Harry S. Truman
            # National Days of Mourning
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Thanksgiving. Fourth Thursday of November
            "2006-11-30",  # November has 5 Thursdays, last Thursday is not a holiday.
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # 2012
            "2012-07-03",
            "2012-11-23",  # Day after Thanksgiving
            "2012-12-24",  # Christmas Eve
            #
            "2013-11-29",  # Day after Thanksgiving, 4 Thursdays, 5 Fridays in month.
            #
            # Until 2013, if Independence Day fell on a Thursday, the market closed
            # early on the Friday. Since 2013 the early close is on the Wednesday.
            "2002-07-05",  # Friday after an Independence Day that fell on a Thursday
            "2013-07-03",  # Wednesday before an Independence Day that fell on Thursday
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(13, "h")

    @pytest.fixture
    def non_early_closes_sample(self):
        yield [
            # Until 2013, if Independence Day fell on a Thursday, the market closed
            # early on the Friday. Since 2013 the early close is on the Wednesday.
            "2002-07-03",  # Wednesday before an Independence Day that fell on Thursday
            "2013-07-05",  # Friday after an Independence Day that fell on Thursday
        ]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(16, "h")
