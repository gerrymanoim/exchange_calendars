import pytest

from exchange_calendars.exchange_calendar_xbog import XBOGExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBaseNew


class TestXBOGCalendar(ExchangeCalendarTestBaseNew):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBOGExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2019-01-01",  # New Year's Day
            "2019-01-07",  # Epiphany
            "2019-03-25",  # St. Joseph's Day
            "2019-04-18",  # Maundy Thursday
            "2019-04-19",  # Good Friday
            "2019-05-01",  # Labour Day
            "2019-06-03",  # Ascension Day
            "2019-06-24",  # Corpus Christi
            "2019-07-01",  # Sacred Heart
            "2018-07-02",  # St. Peter and St. Paul Day
            "2018-07-20",  # Colombian Independence Day
            "2019-08-07",  # Battle of Boyaca
            "2019-08-19",  # Assumption Day
            "2019-10-14",  # Dia de la Raza
            "2019-11-04",  # All Saint's Day
            "2019-11-11",  # Cartagena Independence Day
            "2017-12-08",  # Immaculate Conception
            "2019-12-25",  # Christmas Day
            "2019-12-31",  # Last Trading Day
            #
            # Calendar has many holidays that are observed on the closest future
            # Monday. Ensure the future Monday is a holdiay.
            "2017-01-09",  # Epiphany moved to Monday, Jan 9
            "2019-03-25",  # St. Joseph's Day moved to Monday, Mar 25
            "2018-07-02",  # St. Peter and St. Paul Day moved to Monday, Jul 2
            "2018-08-20",  # Assumption Day moved to Monday, Aug 20
            "2018-10-15",  # Dia de la Raza moved to Monday, Oct 15
            "2018-11-05",  # All Saint's Day moved to Monday, Nov 5
            "2016-11-14",  # Cartagena Independence Day moved to Monday, Nov 14
            #
            # The last trading day of the year is a holiday for XBOG
            "2019-12-31",
            "2018-12-31",
            "2017-12-29",
            "2016-12-30",
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # For holidays that fall on a weekend and are not made up, ensure
            # surrounding days are not treated as holidays.
            # New Years Day on Sunday, Jan 1st
            #   Note: 2011-12-30 is also a holiday (Last Trading Day).
            "2011-12-29",
            "2012-01-02",
            # Labour Day on Sunday, May 1st
            "2016-04-29",
            "2016-05-02",
            # Colombia Independence Day on Saturday, Jul 20
            "2019-07-19",
            "2019-07-22",
            # Battle of Boyaca on Sunday, Aug 7
            "2016-08-05",
            "2016-08-08",
            # Immaculate Conception on Sunday, Dec 8th.
            "2019-12-06",
            "2019-12-09",
            # Christmas on a Sunday
            "2016-12-23",
            "2016-12-26",
            #
            # Calendar has many holidays that are observed on the closest future
            # Monday. Ensure that, if falls on a non-Monday, the prior Monday
            # is not a holiday.
            "2017-01-06",  # Epiphany on Friday, Jan 6
            "2019-03-19",  # St. Joseph's Day on Tuesday, Mar 19
            "2018-06-29",  # St. Peter and St. Paul Day on Friday, Jun 29
            "2018-08-15",  # Assumption Day on Wednesday, Aug 15
            "2018-10-12",  # Dia de la Raza on Friday, Oct 12
            "2018-11-01",  # All Saint's Day on Thursday, Nov 1
            "2016-11-11",  # Cartagena Independence Day on Friday, Nov 11
        ]
