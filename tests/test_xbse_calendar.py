import pytest

from exchange_calendars.exchange_calendar_xbse import XBSEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXBSECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBSEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # XBSE is open from 10:00 to 5:20PM on its longest trading day
        yield 7 + (3 / 4)

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2023-04-17",  # Orthodox Easter
            "2023-04-14",  # Good Friday
            "2021-01-01",  # New Year's Day
            "2021-04-30",  # Orthodox Good Friday
            "2021-06-01",  # Children's day
            "2021-06-21",  # Orthodox Pentecost
            "2021-11-30",  # St. Adnrew's Day
            "2021-12-01",  # National Day
            "2020-01-01",  # New Year's Day
            "2020-01-02",  # New Year's Day
            "2020-01-24",  # Romanian Principalities Unification Day
            "2020-04-17",  # Good Friday
            "2020-04-20",  # Orthodox Easter
            "2020-05-01",  # Labour Day
            "2020-06-01",  # Children's Day
            "2020-06-08",  # Orthodox Pentecost
            "2020-11-30",  # St. Adnrew's day
            "2020-12-01",  # National Day
            "2020-12-25",  # Christmans
            "2019-01-01",  # New Year's Day
            "2019-01-02",  # New Year's Day
            "2019-01-24",  # Romanian Principalities Unification Day
            "2019-04-26",  # Good Friday
            "2019-04-29",  # Orthodox Easter
            "2019-05-01",  # Labour Day
            "2019-06-17",  # Orthodox Pentecost
            "2019-08-15",  # Assumption of Virgin Mary
            "2019-12-25",  # Christmans
            "2019-12-26",  # Christmans
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # Athens Stock Exchange observes Orthodox (or Eastern) Easter,
            # as well as Western Easter. All holidays that are tethered to
            # Easter (i.e. Whit Monday, Good Friday, etc.), are relative to
            # Orthodox Easter. Following checks that Orthodox Easter and
            # related holidays are correct.
            # # Some Orthodox Good Friday dates
            "2002-05-03",
            "2005-04-29",
            "2008-04-25",
            "2009-04-17",
            "2016-04-29",
            "2017-04-14",
            # Some Orthodox Pentecost dates
            "2002-06-24",
            "2005-06-20",
            "2006-06-12",
            "2008-06-16",
            "2013-06-24",
            "2016-06-20",
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # Second New Years Day on Saturday, Jan 2st
            "2021-01-04",
            # Christmas 25th, 26th both holidays, fall Saturday Sunday
            "2021-12-24",
            "2021-12-27",
            # Labour Day on Saturday + Good Friday on Friday + Orthodox Easter on Monday
            "2021-04-29",
            "2021-05-04",
            # Children's Day on Saturday
            "2019-05-31",
            "2019-06-03",
            # Assumption of Virgin Mary on Sunday
            "2021-08-13",
            "2021-08-16",
            # Assumption of Virgin Mary on Saturday
            "2020-08-14",
            "2020-08-17",
        ]
