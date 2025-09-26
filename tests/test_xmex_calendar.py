import pytest

from exchange_calendars.exchange_calendar_xmex import XMEXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXMEXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XMEXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XMEX is open from 8:30AM to 3:00PM.
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2019-01-01",  # New Year's Day
            "2019-02-04",  # Constitution Day
            "2019-03-18",  # Juarez's Birthday
            "2019-04-18",  # Maundy Thursday
            "2019-04-19",  # Good Friday
            "2019-05-01",  # Labour Day
            "2019-09-16",  # Independence Day
            "2018-11-02",  # All Souls' Day
            "2019-11-18",  # Revolution Day
            "2019-12-12",  # Banking Holiday
            "2019-12-25",  # Christmas Day
            "2006-11-02",  # first observance of regular holiday All Soul's Day.
            # Rule changes.
            # Consitution Day. Prior to 2007 observed strictly on February 5th.
            "2004-02-05",  # falls Thursday, otherwise a trading day
            # from 2007 observed on first Monday of February
            "2008-02-04",  # 5th falls on a Tuesday, first Monday is 4th
            # Juarez's Birthday. Prior to 2007 observed strictly on March 21st.
            "2006-03-21",  # falls Tuesday, otherwise a trading day
            # from 2007 observed on third Monday of March.
            "2007-03-19",  # 21st falls on a Wednesday, third Monday is 19th.
            # Revolution Day. Prior to 2007 observed strictly on November 20th.
            "2003-11-20",  # falls Thursday, otherwise a trading day
            # from 2007 obseved on the third Monday of November.
            "2007-11-19",  # 20th falls on a Tuesday, third Monday is 19th.
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield ["2010-09-17"]  # Bicentennial Celebration.

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Day on a Sunday.
            "2016-12-30",
            "2017-01-02",
            # Constitution Day (February 5th) on a Sunday, prior to 2007.
            "2006-02-03",
            "2006-02-06",
            # Juarez's Birthday (March 21st) on a Sunday, prior to 2007.
            "2004-03-19",
            "2004-03-22",
            # Labour Day (May 1st) on a Sunday.
            "2016-04-29",
            "2016-05-02",
            # Independence Day (September 16th) on a Sunday.
            "2018-09-14",
            "2018-09-17",
            # All Souls' Day (November 2nd) on a Saturday.
            "2019-11-01",
            "2019-11-04",
            # Revolution Day (November 20th) on a Sunday, prior to 2007.
            "2005-11-18",
            "2005-11-21",
            # Banking Holiday (December 12th) on a Saturday.
            "2015-12-11",
            "2015-12-14",
            # Christmas on a Sunday.
            "2016-12-23",
            "2016-12-26",
            "2005-11-02",  # All Soul's Day not observed until 2006.
            # Rule changes.
            # Consitution Day. Prior to 2007 observed strictly on February 5th,
            # from 2007 observed on first Monday of February.
            "2006-02-06",  # fell on Sunday, not made up so Monday is not a holiday.
            "2004-02-02",  # prior to rule change first Monday is not a holiday.
            "2008-02-05",  # falls on a Tuesday, post rule change no longer a holiday.
            # Juarez's Birthday. Prior to 2007 observed strictly on March 21st,
            # from 2007 observed on third Monday of March.
            "2006-03-20",  # prior to rule change third Monday is not a holiday.
            "2007-03-21",  # falls on a Wednesday, post rule change no longer a holiday.
            # Revolution Day. Prior to 2007 observed strictly on November 20th,
            # from 2007 obseved on third Monday of November.
            "2003-11-17",  # prior to rule change third Monday is not a holiday.
            "2007-11-20",  # falls on a Tuesday, post rule change no longer a holiday.
        ]
