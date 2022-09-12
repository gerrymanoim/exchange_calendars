import pytest

from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXLONCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XLONExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2012
            "2012-01-02",  # New Year's observed
            "2012-04-06",  # Good Friday
            "2012-04-09",  # Easter Monday
            "2012-05-07",  # May Day
            "2012-06-04",  # Spring Bank Holiday
            "2012-08-27",  # Summer Bank Holiday
            "2012-12-25",  # Christmas
            "2012-12-26",  # Boxing Day
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2002-06-03",  # Spring Bank 2002
            "2002-06-04",  # Golden Jubilee
            "2011-04-29",  # Royal Wedding
            "2012-06-04",  # Spring Bank 2012
            "2012-06-05",  # Diamond Jubilee
            "2020-05-08",  # VE Day
            "2022-09-19",  # Queen Elizabeth Funeral
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        # May Bank Holiday was instead observed on VE Day in 2020.
        yield ["2020-05-04"]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2012-12-24",  # Christmas Eve
            "2012-12-31",  # New Year's Eve
            "2010-12-24",  # Christmas Eve
            "2010-12-31",  # New Year's Eve
            # In Dec 2011, Christmas Eve and NYE are both on a Saturday,
            # so preceding Fridays (the 23rd and 30th) are early closes.
            "2011-12-23",
            "2011-12-30",
        ]
