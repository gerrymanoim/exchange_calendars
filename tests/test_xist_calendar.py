import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xist import XISTExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXISTCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XISTExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XIST is open from 10:00 am to 6:00 pm
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2019-01-01",  # New Year's Day
            "2019-04-23",  # Natl Sov and Children's Day
            "2019-05-01",  # Labour Day
            "2017-05-19",  # CAYS Day
            "2019-06-04",  # Eid al Fitr Day 1
            "2019-06-05",  # Eid al Fitr Day 2
            "2019-06-06",  # Eid al Fitr Day 3
            "2019-07-15",  # Dem and Natl Unity Day
            "2016-09-12",  # Eid al Adha Day 1
            "2016-09-13",  # Eid al Adha Day 2
            "2016-09-14",  # Eid al Adha Day 3
            "2016-09-15",  # Eid al Adha Day 4
            "2019-08-30",  # Victory Day
            "2019-10-29",  # Republic Day
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # Miscellaneous closures
            "2002-01-04",  # Market Holiday
            "2003-11-21",  # Terror attacks
            "2004-01-23",  # Bad weather
            "2004-12-30",  # Closure for redenomination
            "2004-12-31",  # Closure for redenomination
            # Eid al Adha and Eid al Fitr extra closures
            "2003-02-14",  # Eid al Adha extra holiday
            "2003-11-24",  # Eid al Fitr extra holiday
            "2003-11-28",  # Eid al Fitr extra holiday
            "2006-01-13",  # Eid al Adha extra holiday
            "2023-02-08",  # Trade suspension after earthquake
            "2023-02-09",  # Trade suspension after earthquake
            "2023-02-10",  # Trade suspension after earthquake
            "2023-02-13",  # Trade suspension after earthquake
            "2023-02-14",  # Trade suspension after earthquake
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Day on Sunday, Jan 1st.
            "2011-12-30",
            "2012-01-02",
            # Natl Sovereignty and Children's Day on Sunday, Apr 23rd.
            "2017-04-21",
            "2017-04-24",
            # Labour Day on Sunday, May 1st.
            "2016-04-29",
            "2016-05-02",
            # Com. of Attaturk Youth and Sport's Day on Saturday, May 19th.
            "2018-05-18",
            "2018-05-21",
            # Eid Al Fitr (Day 3) on Sunday, Jun 17th (Friday is a holiday).
            "2018-06-18",
            # Democracy and National Unity Day on Sunday, Jul 15th.
            "2018-08-13",
            "2018-07-16",
            # Eid Al Adha (Day 1) on Sunday, Aug 11th (Monday is a holiday).
            "2019-08-09",
            # Victory Day on Saturday, Aug 30th.
            "2014-08-29",
            "2014-09-01",
            # Republic Day on Saturday, Oct 29th.
            "2016-10-28",
            "2016-10-31",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2019-10-28",  # Day before Republic Day.
            "2019-06-03",  # Day before Eid al Adha.
            "2018-08-20",  # Day before Eid al Adha.
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=12, minutes=30)
