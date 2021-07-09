from unittest import TestCase

import pandas as pd
from pytz import UTC

from exchange_calendars.exchange_calendar_xtks import XTKSExchangeCalendar
from exchange_calendars.exchange_calendar import SUNDAY, WEDNESDAY
from exchange_calendars.xtks_holidays import (
    AutumnalEquinoxes,
    ChildrensDay,
    CitizensHolidaySilverWeek,
    ConstitutionMemorialDay2007Onwards,
    ConstitutionMemorialDayThrough2006,
    EmperorAkihitoBirthday,
    GreeneryDay2007Onwards,
    RespectForTheAgedDay2003Onwards,
)

from .test_exchange_calendar import ExchangeCalendarTestBase


class XTKSCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xtks"
    calendar_class = XTKSExchangeCalendar

    START_BOUND = pd.Timestamp("2000-01-01", tz="UTC")
    MAX_SESSION_HOURS = 6
    HAVE_EARLY_CLOSES = False

    def test_2012(self):
        expected_holidays_2012 = [
            pd.Timestamp("2012-01-01", tz=UTC),  # New Year's holiday
            pd.Timestamp("2012-01-02", tz=UTC),  # New Year's holiday
            pd.Timestamp("2012-01-03", tz=UTC),  # New Year's holiday
            pd.Timestamp("2012-01-09", tz=UTC),  # Coming of Age Day
            # National Foundation Day was on a Saturday so it is ignored
            pd.Timestamp("2012-03-20", tz=UTC),  # Vernal Equinox
            pd.Timestamp("2012-04-30", tz=UTC),  # Showa Day Observed
            pd.Timestamp("2012-05-03", tz=UTC),  # Constitution Memorial Day
            pd.Timestamp("2012-05-04", tz=UTC),  # Greenery Day
            # Children's Day was on a Saturday so it is ignored
            pd.Timestamp("2012-07-16", tz=UTC),  # Marine Day
            pd.Timestamp("2012-09-17", tz=UTC),  # Respect for the Aged Day
            # The Autumnal Equinox was on a Saturday so it is ignored
            pd.Timestamp("2012-10-08", tz=UTC),  # Health and Sports Day
            # Culture Day was on a Saturday so it is ignored
            pd.Timestamp("2012-11-23", tz=UTC),  # Labor Thanksgiving Day
            pd.Timestamp("2012-12-24", tz=UTC),  # Emperor Birthday Observed
            pd.Timestamp("2012-12-31", tz=UTC),  # New Year's holiday
        ]

        for session_label in expected_holidays_2012:
            self.assertNotIn(session_label, self.calendar.all_sessions)

    def test_golden_week(self):
        # from 2000 to 2006 May 4 was an unnamed citizen's holiday because
        # it was between Constitution Memorial Day and Children's Day
        consitution_memorial_days = ConstitutionMemorialDayThrough2006.dates(
            "2000-01-01", "2007-01-01"
        )
        childrens_days = ChildrensDay.dates("2000-01-01", "2007-01-01")

        for cm_day, childrens_day in zip(consitution_memorial_days, childrens_days):

            # if there is only one day between Constitution Memorial
            # Day and Children's Day, that day should be a holiday
            if childrens_day - cm_day != pd.Timedelta(days=2):
                continue

            citizens_holiday = cm_day + pd.Timedelta(days=1)

            self.assertNotIn(cm_day, self.calendar.all_sessions)
            self.assertNotIn(citizens_holiday, self.calendar.all_sessions)
            self.assertNotIn(childrens_day, self.calendar.all_sessions)

        # from 2007 onwards, Greenery Day was moved to May 4
        consitution_memorial_days = ConstitutionMemorialDay2007Onwards.dates(
            "2007-01-01", "2019-01-01"
        )
        greenery_days = GreeneryDay2007Onwards.dates("2007-01-01", "2019-01-01")
        childrens_days = ChildrensDay.dates("2007-01-01", "2019-01-01")

        # In 2008, Greenery Day is on a Sunday, and Children's Day
        # is on a Monday, so Greenery Day should be observed on Tuesday
        #       May 2008
        # Su Mo Tu We Th Fr Sa
        #  4  5  6  7  8  9 10
        self.assertIn(pd.Timestamp("2008-05-05"), childrens_days)
        self.assertIn(pd.Timestamp("2008-05-06"), greenery_days)

        # In 2009, Consitution Memorial Day should be observed on Wednesday,
        # since it is the next weekday that is not a holiday
        #       May 2009
        # Su Mo Tu We Th Fr Sa
        #                 1  2
        #  3  4  5  6  7  8  9
        self.assertIn(pd.Timestamp("2009-05-04"), greenery_days)
        self.assertIn(pd.Timestamp("2009-05-05"), childrens_days)
        self.assertIn(pd.Timestamp("2009-05-06"), consitution_memorial_days)

        # In 2012, Children's Day should not be observed because it falls
        # on a Saturday
        #       May 2012
        # Su Mo Tu We Th Fr Sa
        #        1  2  3  4  5
        #  6  7  8  9 10 11 12
        self.assertIn(pd.Timestamp("2012-05-03"), consitution_memorial_days)
        self.assertIn(pd.Timestamp("2012-05-04"), greenery_days)

        # In 2013, May 3 and 6 should be a holiday
        #       May 2013
        # Su Mo Tu We Th Fr Sa
        #           1  2  3  4
        #  5  6  7  8  9 10 11
        self.assertIn(pd.Timestamp("2013-05-03"), consitution_memorial_days)
        self.assertIn(pd.Timestamp("2013-05-06"), childrens_days)

    def test_silver_week(self):
        def day_before(dt):
            return dt - pd.Timedelta(days=1)

        # Make sure that every Tuesday between Respect for the Aged Day and
        # the Autumnal Equinox is also a holiday
        silver_week_citizens_holidays = []
        for equinox in AutumnalEquinoxes:
            if equinox.dayofweek == WEDNESDAY:
                silver_week_citizens_holidays.append(day_before(equinox))

        expected_silver_week_holidays = CitizensHolidaySilverWeek
        self.assertEqual(silver_week_citizens_holidays, expected_silver_week_holidays)

        respect_for_the_aged_days = RespectForTheAgedDay2003Onwards.dates(
            "2003-01-01", AutumnalEquinoxes[-1]
        )

        for citizens_holiday in silver_week_citizens_holidays:
            self.assertNotIn(citizens_holiday, self.calendar.all_sessions)
            # the day before the citizen's holiday should be Respect
            # for the Aged Day
            respect_for_the_aged_day = day_before(citizens_holiday)
            self.assertNotIn(respect_for_the_aged_day, self.calendar.all_sessions)
            self.assertIn(respect_for_the_aged_day, respect_for_the_aged_days)

    def test_emperors_birthday(self):

        # The Emperor's birthday should be celebrated every year except
        # for 2019
        expected_birthdays = EmperorAkihitoBirthday.dates("1990-01-01", "2020-01-01")

        for year in range(1990, 2019):
            birthday = pd.Timestamp("{}-12-23".format(year))
            if birthday.dayofweek == SUNDAY:
                birthday += pd.Timedelta(days=1)

            self.assertIn(birthday, expected_birthdays)

        self.assertNotIn(pd.Timestamp("2019-12-23"), expected_birthdays)

    def test_mountain_day(self):
        # Mountain Day was not celebrated prior to 2016.
        self.assertIn(pd.Timestamp("2015-08-11"), self.calendar.all_sessions)

        # First celebrated and observed in 2016.
        self.assertNotIn(
            pd.Timestamp("2016-08-11"),
            self.calendar.all_sessions,
        )

        #     August 2019
        # Su Mo Tu We Th Fr Sa
        #              1  2  3
        #  4  5  6  7  8  9 10
        # 11 12 13 14 15 16 17
        # 18 19 20 21 22 23 24
        # 25 26 27 28 29 30 31
        #
        # Falls on a Sunday in 2019, so it is observed on Monday.
        self.assertNotIn(
            pd.Timestamp("2019-08-12"),
            self.calendar.all_sessions,
        )

    def test_2019_adhocs(self):
        # Check if adhoc holidays in 2019 are observed
        expected_holidays = [
            pd.Timestamp("2019-04-30", tz=UTC),  # Abdication Day
            pd.Timestamp("2019-05-01", tz=UTC),  # Accession Day
            pd.Timestamp("2019-05-02", tz=UTC),  # Citizen's Holiday
            pd.Timestamp("2019-10-22", tz=UTC),  # Enthronment Ceremony
        ]

        for holiday_label in expected_holidays:
            self.assertNotIn(holiday_label, self.calendar.all_sessions)

    def test_2020(self):
        expected_holidays_2020 = [
            pd.Timestamp("2020-01-01", tz=UTC),  # New Year's holiday
            pd.Timestamp("2020-01-02", tz=UTC),  # New Year's holiday
            pd.Timestamp("2020-01-03", tz=UTC),  # New Year's holiday
            pd.Timestamp("2020-01-13", tz=UTC),  # Coming of Age Day
            pd.Timestamp("2020-02-11", tz=UTC),  # National Foundation Day
            pd.Timestamp("2020-02-23", tz=UTC),  # Emperor's Birthday
            pd.Timestamp("2020-02-24", tz=UTC),  # Emperor's Birthday observed
            pd.Timestamp("2020-03-20", tz=UTC),  # Vernal Equinox
            pd.Timestamp("2020-04-29", tz=UTC),  # Showa Day
            pd.Timestamp("2020-05-03", tz=UTC),  # Constitution Memorial Day
            pd.Timestamp("2020-05-04", tz=UTC),  # Greenery Day
            pd.Timestamp("2020-05-05", tz=UTC),  # Children's Day
            pd.Timestamp("2020-05-06", tz=UTC),  # Constitution Memorial Day
            # observed
            pd.Timestamp("2020-07-23", tz=UTC),  # Marine Day
            pd.Timestamp("2020-07-24", tz=UTC),  # Sports Day
            pd.Timestamp("2020-08-10", tz=UTC),  # Mountain Day
            pd.Timestamp("2020-09-21", tz=UTC),  # Respect for the Aged Day
            pd.Timestamp("2020-09-22", tz=UTC),  # Autumnal Equinox
            pd.Timestamp("2020-11-03", tz=UTC),  # Culture Day
            pd.Timestamp("2020-11-23", tz=UTC),  # Labor Thanksgiving Day
            pd.Timestamp("2020-12-31", tz=UTC),  # New Year's holiday
        ]

        for session_label in expected_holidays_2020:
            self.assertNotIn(session_label, self.calendar.all_sessions)

    def test_2021(self):
        expected_holidays_2021 = [
            pd.Timestamp("2021-01-01", tz="UTC"),  # New Year's Day
            pd.Timestamp("2021-01-02", tz="UTC"),  # Market Holiday
            pd.Timestamp("2021-01-03", tz="UTC"),  # Market Holiday
            pd.Timestamp("2021-01-11", tz="UTC"),  # Coming of Age Day
            pd.Timestamp("2021-02-11", tz="UTC"),  # National Foundation Day
            pd.Timestamp("2021-02-23", tz="UTC"),  # Emperor's Birthday
            pd.Timestamp("2021-03-20", tz="UTC"),  # Vernal Equinox
            pd.Timestamp("2021-04-29", tz="UTC"),  # Showa Day
            pd.Timestamp("2021-05-03", tz="UTC"),  # Constitution Memorial Day
            pd.Timestamp("2021-05-04", tz="UTC"),  # Greenery Day
            pd.Timestamp("2021-05-05", tz="UTC"),  # Children's Day
            pd.Timestamp("2021-07-22", tz="UTC"),  # Marine Day
            pd.Timestamp("2021-07-23", tz="UTC"),  # Sports Day
            pd.Timestamp("2021-08-08", tz="UTC"),  # Mountain Day
            pd.Timestamp("2021-08-09", tz="UTC"),  # Mountain Day observed
            pd.Timestamp("2021-09-20", tz="UTC"),  # Respect for the Aged Day
            pd.Timestamp("2021-09-23", tz="UTC"),  # Autumnal Equinox
            pd.Timestamp("2021-11-03", tz="UTC"),  # Culture Day
            pd.Timestamp("2021-11-23", tz="UTC"),  # Labor Thanksgiving Day
            pd.Timestamp("2021-12-31", tz="UTC"),  # Market Holiday
        ]

        for session_label in expected_holidays_2021:
            self.assertNotIn(session_label, self.calendar.all_sessions)
