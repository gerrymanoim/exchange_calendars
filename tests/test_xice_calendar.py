import pytest

from exchange_calendars.exchange_calendar_xice import XICEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXICECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XICEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XICE is open from 9:30 am to 3:30 pm.
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2018
            "2018-01-01",  # New Year's Day
            "2018-03-29",  # Maundy Thursday
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-04-19",  # First Day of Summer
            "2018-05-01",  # Labour Day
            "2018-05-10",  # Ascension Day
            "2018-05-21",  # Whit Monday
            "2019-06-17",  # National Day
            "2018-08-06",  # Commerce Day
            "2018-12-24",  # Christmas Eve
            "2018-12-25",  # Christmas Day
            "2018-12-26",  # Boxing Day
            "2018-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield []

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # In 2016, Labour Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2016-04-29",
            "2016-05-02",
            # In 2018, National Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2018-06-15",
            "2018-06-18",
            # In 2010, Christmas fell on a Saturday, meaning Boxing Day fell on
            # a Sunday. The market should thus be open on the following Monday.
            "2010-12-27",
            # In 2017, New Year's Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2016-12-30",
            "2017-01-02",
        ]
