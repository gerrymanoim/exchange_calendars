import pytest

from exchange_calendars.exchange_calendar_xbkk import XBKKExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBaseNew


class TestXBKKCalendar(ExchangeCalendarTestBaseNew):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBKKExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2019-01-01",  # New Year's Day
            "2019-02-19",  # Makha Bucha
            "2018-04-06",  # Chakri Memorial Day
            "2016-04-13",  # Songkran Festival
            "2016-04-14",  # Songkran Festival
            "2016-04-15",  # Songkran Festival
            "2019-05-01",  # Labour Day
            "2016-05-05",  # Coronation Day
            "2019-05-20",  # Vesak
            "2019-06-03",  # Queen's Birthday
            "2019-07-16",  # Asanha Bucha
            "2017-07-28",  # King's Birthday
            "2019-08-12",  # Queen Mother's Birthday
            "2017-10-13",  # Passing of King Bhumibol
            "2019-10-23",  # Chulalongkorn Day
            "2019-12-05",  # King Bhumibol's Birthday
            "2019-12-10",  # Thailand Constitution Day
            "2019-12-31",  # New Year's Eve
            #
            # Holidays falling on a weekend and subsequently made up.
            # New Year's Eve on a Saturday and New Year's Day on a Sunday.
            "2017-01-02",  # following Monday a holiday...
            "2017-01-03",  # and following Tuesday.
            "2011-01-03",  # New Year's Day on a Saturday.
            "2019-04-08",  # Chakri Memorial Day (April 6th) on a Saturday.
            # Songkran Festival Days 2 and 3 (Saturday April 14th and Sunday 15th)...
            "2018-04-16",  # although only one day made up, on Monday.
            "2016-05-02",  # Labour Day (May 1st) on a Sunday.
            "2019-05-06",  # Coronation Day (May 5th) on a Sunday.
            "2014-05-05",  # Coronation Day (May 4th) on a Sunday.
            "2019-07-29",  # King's Birthday (July 28th) on a Sunday.
            "2018-08-13",  # Queen Mother's Birthday (August 12th) on a Sunday.
            "2019-10-14",  # The Passing of King Bhumibol (October 13th) on a Sunday.
            "2016-10-24",  # Chulalongkorn Day (October 23rd) on a Sunday.
            "2015-12-07",  # King Bhumibol's Birthday (December 5th) on a Saturday.
            "2017-12-11",  # Thailand Constitution Day (December 10th) on a Sunday.
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # "bridge days" where a Monday or Friday is made into a holiday
            # to fill gap between weekend and a holiday on Tuesday or Thursday.
            "2015-01-02",  # New Year's is a Thusday, so Friday is bridge day.
            "2013-12-30",  # New Year's Eve is a Tuesday, so Monday is bridge day.
            "2016-07-18",  # Asanha Bucha is a Tuesday, so Monday is a bridge day.
            "2010-08-13",  # Queen's B'day a Thursday, so Friday is a bridge day.
            "2016-05-06",  # Coronation Day a Thursday, so Friday is a bridge day.
            "2011-05-16",  # Vesak Day a Tuesday, so the Monday is a bridge day.
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # When Songkran Festival Days 2 and 3 (April 14th and 15th) fall on
            # a Saturday and Sunday, only the next Monday is a holiday...
            "2018-04-17",  # Tuesday 17th is not a holiday.
            # When the last day of Songkran Festival (April 15th) falls on a
            # Saturday...
            "2017-04-17",  # not made up - Monday is not a holdiay.
        ]
