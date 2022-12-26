import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xtks import XTKSExchangeCalendar
from exchange_calendars.exchange_calendar import SUNDAY, WEDNESDAY
from exchange_calendars.xtks_holidays import (
    AutumnalEquinoxes,
    ChildrensDay,
    CitizensHolidaySilverWeek,
    ConstitutionMemorialDay,
    EmperorAkihitoBirthday,
    GreeneryDay2007Onwards,
    RespectForTheAgedDay2003Onwards,
)
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T

# NOTE: A couple of dedicated tests, and sanity tests in fixtures, test
# holidays imported from xtks_holidays. These tests would probably be
# better placed on a spearate test module, or at least to a separate
# class on this module.


class TestXTKSCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XTKSExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6

    @pytest.fixture
    def start_bound(self):
        yield T("1997-01-01")

    @pytest.fixture  # Calendar-specific fixture
    def silver_week_holidays(self):
        """List of pd.Timestamp representing Citizens Day and
        Respect for the Aged Day holidays of silver week.
        """

        def day_before(dt):
            return dt - pd.Timedelta(days=1)

        # Make sure that every Tuesday between Respect for the Aged Day and
        # the Autumnal Equinox is a citizen's holiday
        citizens_holidays = []
        for equinox in AutumnalEquinoxes:
            # It is unusual for September to get this extra holiday
            # so the presence of a "silver week" was not widely noted before 2009
            if equinox < pd.Timestamp("2009-01-01"):
                continue
            if equinox.dayofweek == WEDNESDAY:
                citizens_holidays.append(day_before(equinox))

        expected_citizens_holidays = CitizensHolidaySilverWeek
        # NOTE: Tests of imported holidays should probably be on a separate test module.
        assert citizens_holidays == expected_citizens_holidays  # Sanity check

        respect_for_the_aged_days = RespectForTheAgedDay2003Onwards.dates(
            "2003-01-01", AutumnalEquinoxes[-1]
        )

        rftad_holidays = []
        for citizens_holiday in citizens_holidays:
            # the day before the citizen's holiday should be Respect for the Aged Day.
            respect_for_the_aged_day = day_before(citizens_holiday)
            rftad_holidays.append(respect_for_the_aged_day)
            # NOTE: Tests of imported holidays should probably be on a separate module.
            assert respect_for_the_aged_day in respect_for_the_aged_days  # Sanity check

        yield citizens_holidays + rftad_holidays

    @pytest.fixture  # Calendar-specific fixture
    def golden_week_holidays(self):
        """List of pd.Timestamp representing citizen's holidays in Golden Week
        prior to 2007.
        """
        # from 1997 to 2006 May 4 was an unnamed citizen's holiday between
        # Constitution Memorial Day and Children's Day
        start, end = "1997-01-01", "2007-01-01"
        consitution_memorial_days = ConstitutionMemorialDay.dates(start, end)
        childrens_days = ChildrensDay.dates(start, end)
        citizens_days = []
        for cm_day, childrens_day in zip(consitution_memorial_days, childrens_days):
            # if there is only one day between Constitution Memorial
            # Day and Children's Day, that day should be a holiday
            if childrens_day - cm_day != pd.Timedelta(days=2):
                continue
            citizens_days.append(cm_day + pd.Timedelta(days=1))
        yield citizens_days

    @pytest.fixture
    def regular_holidays_sample(self, silver_week_holidays, golden_week_holidays):
        by_year = [
            # 2012
            "2012-01-01",  # New Year's holiday
            "2012-01-02",  # New Year's holiday
            "2012-01-03",  # New Year's holiday
            "2012-01-09",  # Coming of Age Day
            # National Foundation Day was on a Saturday so it is ignored
            "2012-03-20",  # Vernal Equinox
            "2012-04-30",  # Showa Day Observed
            "2012-05-03",  # Constitution Memorial Day
            "2012-05-04",  # Greenery Day
            # Children's Day was on a Saturday so it is ignored
            "2012-07-16",  # Marine Day
            "2012-09-17",  # Respect for the Aged Day
            # The Autumnal Equinox was on a Saturday so it is ignored
            "2012-10-08",  # Health and Sports Day
            # Culture Day was on a Saturday so it is ignored
            "2012-11-23",  # Labor Thanksgiving Day
            "2012-12-24",  # Emperor Birthday Observed
            "2012-12-31",  # New Year's holiday
            #
            # 2020
            "2020-01-01",  # New Year's holiday
            "2020-01-02",  # New Year's holiday
            "2020-01-03",  # New Year's holiday
            "2020-01-13",  # Coming of Age Day
            "2020-02-11",  # National Foundation Day
            "2020-02-23",  # Emperor's Birthday
            "2020-02-24",  # Emperor's Birthday observed
            "2020-03-20",  # Vernal Equinox
            "2020-04-29",  # Showa Day
            "2020-05-03",  # Constitution Memorial Day
            "2020-05-04",  # Greenery Day
            "2020-05-05",  # Children's Day
            "2020-05-06",  # Constitution Memorial Day
            # observed
            "2020-07-23",  # Marine Day
            "2020-07-24",  # Sports Day
            "2020-08-10",  # Mountain Day
            "2020-09-21",  # Respect for the Aged Day
            "2020-09-22",  # Autumnal Equinox
            "2020-11-03",  # Culture Day
            "2020-11-23",  # Labor Thanksgiving Day
            "2020-12-31",  # New Year's holiday
            #
            # 2021
            "2021-01-01",  # New Year's Day
            "2021-01-02",  # Market Holiday
            "2021-01-03",  # Market Holiday
            "2021-01-11",  # Coming of Age Day
            "2021-02-11",  # National Foundation Day
            "2021-02-23",  # Emperor's Birthday
            "2021-03-20",  # Vernal Equinox
            "2021-04-29",  # Showa Day
            "2021-05-03",  # Constitution Memorial Day
            "2021-05-04",  # Greenery Day
            "2021-05-05",  # Children's Day
            "2021-07-22",  # Marine Day
            "2021-07-23",  # Sports Day
            "2021-08-08",  # Mountain Day
            "2021-08-09",  # Mountain Day observed
            "2021-09-20",  # Respect for the Aged Day
            "2021-09-23",  # Autumnal Equinox
            "2021-11-03",  # Culture Day
            "2021-11-23",  # Labor Thanksgiving Day
            "2021-12-31",  # Market Holiday
            #
            # 2022
            "2022-01-01",  # New Year's Day
            "2022-01-02",  # Market Holiday
            "2022-01-03",  # Market Holiday
            "2022-01-10",  # Coming of Age Day
            "2022-02-11",  # National Foundation Day #
            "2022-02-23",  # Emperor's Birthday
            "2022-03-21",  # Vernal Equinox
            "2022-04-29",  # Showa Day
            "2022-05-03",  # Constitution Memorial Day
            "2022-05-04",  # Greenery Day
            "2022-05-05",  # Children's Day
            "2022-07-18",  # Marine Day
            "2022-08-11",  # Mountain Day
            "2022-09-19",  # Respect for the Aged Day
            "2022-09-23",  # Autumnal Equinox
            "2022-10-10",  # Sports Day
            "2022-11-03",  # Culture Day
            "2022-11-23",  # Labor Thanksgiving Day
            "2022-12-31",  # Market Holiday
            #
            # 2023
            "2023-01-01",  # New Year's Day
            "2023-01-02",  # Market Holiday
            "2023-01-03",  # Market Holiday
            "2023-01-09",  # Coming of Age Day
            "2023-02-11",  # National Foundation Day #
            "2023-02-23",  # Emperor's Birthday
            "2023-03-21",  # Vernal Equinox
            "2023-04-29",  # Showa Day
            "2023-05-03",  # Constitution Memorial Day
            "2023-05-04",  # Greenery Day
            "2023-05-05",  # Children's Day
            "2023-07-17",  # Marine Day
            "2023-08-11",  # Mountain Day
            "2023-09-18",  # Respect for the Aged Day
            "2023-09-23",  # Autumnal Equinox
            "2023-10-09",  # Sports Day
            "2023-11-03",  # Culture Day
            "2023-11-23",  # Labor Thanksgiving Day
            "2023-12-31",  # Market Holiday
            # Mountain Day 11th August, observed from 2016.
            "2016-08-11",
            "2019-08-12",  # Falls on Sunday, made up on Monday.
        ]

        others = silver_week_holidays + golden_week_holidays
        others = [day.strftime("%Y-%m-%d") for day in others]

        yield by_year + others

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # 2019
            "2019-04-30",  # Abdication Day
            "2019-05-01",  # Accession Day
            "2019-05-02",  # Citizen's Holiday
            "2019-10-22",  # Enthronment Ceremony
            #
            "2020-10-01",  # equity trading system failure
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2015-08-11",  # Mountain Day not observed until to 2016.
        ]

    # Calendar-specific tests

    def test_golden_week_holidays(self):
        # NOTE: This tests imported holidays rather than the XTKS calendar.
        # This test should probably be on a separate test module (together with other
        # such tests here and the sanity checks within fixtures).

        # from 2007 onwards, Greenery Day was moved to May 4
        start, end = "2007-01-01", "2019-01-01"
        consitution_memorial_days = ConstitutionMemorialDay.dates(start, end)
        greenery_days = GreeneryDay2007Onwards.dates(start, end)
        childrens_days = ChildrensDay.dates(start, end)

        # In 2008, Greenery Day is on a Sunday, and Children's Day
        # is on a Monday, so Greenery Day should be observed on Tuesday
        #       May 2008
        # Su Mo Tu We Th Fr Sa
        #  4  5  6  7  8  9 10
        assert pd.Timestamp("2008-05-05") in childrens_days
        assert pd.Timestamp("2008-05-06") in greenery_days

        # In 2009, Consitution Memorial Day should be observed on Wednesday,
        # since it is the next weekday that is not a holiday
        #       May 2009
        # Su Mo Tu We Th Fr Sa
        #                 1  2
        #  3  4  5  6  7  8  9
        assert pd.Timestamp("2009-05-04") in greenery_days
        assert pd.Timestamp("2009-05-05") in childrens_days
        assert pd.Timestamp("2009-05-06") in consitution_memorial_days

        # In 2012, Children's Day should not be observed because it falls
        # on a Saturday
        #       May 2012
        # Su Mo Tu We Th Fr Sa
        #        1  2  3  4  5
        #  6  7  8  9 10 11 12
        assert pd.Timestamp("2012-05-03") in consitution_memorial_days
        assert pd.Timestamp("2012-05-04") in greenery_days

        # In 2013, May 3 and 6 should be a holiday
        #       May 2013
        # Su Mo Tu We Th Fr Sa
        #           1  2  3  4
        #  5  6  7  8  9 10 11
        assert pd.Timestamp("2013-05-03") in consitution_memorial_days
        assert pd.Timestamp("2013-05-06") in childrens_days

    def test_emperors_birthday(self):
        # NOTE: This tests imported holidays rather than the XTKS calendar.
        # This test should probably be on a separate test module (together with other
        # such tests here and the sanity checks within fixtures).

        # The Emperor's birthday should be celebrated every year except
        # for 2019
        expected_birthdays = EmperorAkihitoBirthday.dates("1990-01-01", "2020-01-01")

        for year in range(1990, 2019):
            birthday = pd.Timestamp("{}-12-23".format(year))
            if birthday.dayofweek == SUNDAY:
                birthday += pd.Timedelta(days=1)
            assert birthday in expected_birthdays

        assert pd.Timestamp("2019-12-23") not in expected_birthdays
