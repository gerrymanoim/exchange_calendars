import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xlis import XLISExchangeCalendar
from .test_exchange_calendar import EuronextCalendarTestBase


class TestXLISCalendar(EuronextCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XLISExchangeCalendar

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=13, minutes=5)

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(hours=16, minutes=30)

    @pytest.fixture
    def additional_regular_holidays_sample(self):
        yield [
            # Final observance of these regular holidays
            "2002-02-12",  # Carnival
            "2002-05-30",  # Corpus Christi Day
            "2002-04-25",  # Liberty Day
            "2002-06-10",  # Portugal Day
            "2001-06-13",  # Saint Anthony's Day
            "2002-08-15",  # Assumption Day
            "2001-10-05",  # Republic Day
            "2002-11-01",  # All Saints Day
            "2000-12-01",  # Independence Day
            "2000-12-08",  # Immaculate Conception
            "2002-12-24",  # Christmas Eve
        ]

    @pytest.fixture
    def additional_non_holidays_sample(self):
        yield [
            # First year when previous regular holiday no longer observed
            "2003-03-04",  # Carnival
            "2003-06-16",  # Corpus Christi Day
            "2003-04-25",  # Liberty Day
            "2003-06-10",  # Portugal Day
            "2002-06-13",  # Saint Anthony's Day
            "2003-08-15",  # Assumption Day
            "2004-10-05",  # Republic Day
            "2004-11-01",  # All Saints Day
            "2003-12-01",  # Independence Day
            "2003-12-08",  # Immaculate Conception
            "2003-12-24",  # Christmas Eve
        ]
