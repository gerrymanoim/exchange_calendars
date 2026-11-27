from __future__ import annotations

import functools
from typing import TYPE_CHECKING

import pandas as pd
from pandas.tseries.holiday import Holiday, previous_friday
from pyluach import dates, hebrewcal

if TYPE_CHECKING:
    from collections.abc import Callable

# Auxiliary functions to get Hebrew dates for holidays observed by TASE for a
# given Hebrew calendar year. These are just the raw dates with no adjustments
# applied.
#
# Note: pyluach uses the biblical month numbering scheme where the year is
# incremented when moving from the month of Elul (6) to Tishrei (7). See also
# https://en.wikipedia.org/wiki/Hebrew_calendar.


def _purim(year):
    """
    Return the Hebrew date for Purim in the given Hebrew year.
    """
    # Purim is observed in Adar (12), or Adar II (13) if in a leap year.
    return dates.HebrewDate(year.year, 13 if year.leap else 12, 14)


def _passover(year):
    """
    Return the Hebrew date for the first day of Passover in the given Hebrew
    year.
    """
    return dates.HebrewDate(year.year, 1, 15)


def _memorial_day(year):
    """
    Return the Hebrew date for Memorial Day in the given Hebrew year.

    If either Memorial Day (MD) or Independence Day (ID) were to interfere with Sabbat,
    including night before, then they are shifted forward or backward to avoid Sabbat.
    ID always celebrated day after MD.
    Wiki: https://en.wikipedia.org/wiki/Yom_HaZikaron#Timing
    Better explanation: https://ph.yhb.org.il/en/05-04-09
    """
    d = dates.HebrewDate(year.year, 2, 4)
    if d.weekday() == 1:
        # MD on Sunday => shift forward to Monday
        d = dates.HebrewDate(year.year, 2, 5)
    elif d.weekday() == 6:
        # MD on Friday => ID on Sabbat => shift back 2 days
        d = dates.HebrewDate(year.year, 2, 2)
    elif d.weekday() == 5:
        # MD on Thursday => ID night before Sabbat => shift back 1 day
        d = dates.HebrewDate(year.year, 2, 3)

    return d


def _pentecost(year):
    """
    Return the Hebrew date for Pentecost in the given Hebrew year.
    """
    return dates.HebrewDate(year.year, 3, 6)


def _fast_day(year):
    """
    Return the Hebrew date for Tisha B'Av in the given Hebrew year.
    """
    return dates.HebrewDate(year.year, 5, 9)


def _new_year(year):
    """
    Return the Hebrew date for the first day of a new year in the given Hebrew
    year.
    """
    return dates.HebrewDate(year.year, 7, 1)


def _yom_kippur(year):
    """
    Return the Hebrew date for Yom Kippur in the given Hebrew year.
    """
    return dates.HebrewDate(year.year, 7, 10)


def _sukkoth(year):
    """
    Return the Hebrew date for Sukkoth in the given Hebrew year.
    """
    return dates.HebrewDate(year.year, 7, 15)


def _simchat_torah(year):
    """
    Return the Hebrew date for Simchat Torah in the given Hebrew year.
    """
    return dates.HebrewDate(year.year, 7, 22)


def _hebrew_year(year):
    """
    Return the Hebrew calendar year that corresponds to 1st January of the
    given Gregorian calendar year.

    1st January of any Gregorian calendar year, say x, always falls into the
    month of Tevet (10) or Shevat (11) of some Hebrew year f(x). Also, we have
    f(x+1) = f(x) + 1, so that any year in the Gregorian calendar always
    overlaps with two consecutive years in the Hebrew calendar and vice versa.
    """
    return hebrewcal.Year(dates.GregorianDate(year, 1, 1).to_heb().year)


# Auxilliary functions to calculate Gregorian dates for holidays observed by
# TASE for a given Gregorian calendar year. Adjustments are also applied.


def purim(year):
    """
    Return the Gregorian date for Purim in the given Gregorian calendar year.
    """
    return _purim(_hebrew_year(year)).to_greg()


def passover(year):
    """
    Return the Gregorian date for the first day of Passover in the given
    Gregorian calendar year.
    """
    return _passover(_hebrew_year(year)).to_greg()


def memorial_day(year):
    """
    Return the Gregorian date for Memorial Day in the given Gregorian calendar
    year.
    """

    # Regular Memorial Day date.
    d = _memorial_day(_hebrew_year(year)).to_greg()

    # Reschedule to avoid Sabbath desecration, maybe.
    if d.weekday() == 5:
        # Falls on a Thursday, so Independency Day falls on the Friday.
        # Moved down by one day.
        return d - 1
    if d.weekday() == 6:
        # Falls on a Friday, so Independence Day falls on the Saturday.
        # Moved down by two days.
        return d - 2
    if d.weekday() == 7:
        # Falls on a Saturday, therefore moved up by one day.
        return d + 1
    return d


def pentecost(year):
    """
    Return the Gregorian date for Pentecost in the given Gregorian calendar
    year.
    """
    return _pentecost(_hebrew_year(year)).to_greg()


def fast_day(year):
    """
    Return the Gregorian date for Tisha B'Av in the given Gregorian calendar
    year.
    """
    d = _fast_day(_hebrew_year(year)).to_greg()

    # Reschedule if it falls on Sabbath (Saturday), maybe.
    if d.weekday() == 7:
        # Falls on a Saturday, therefore moved up by one day.
        return d + 1
    return d


def new_year(year):
    """
    Return the Gregorian date for the first day of a new year in the given
    Gregorian calendar year.
    """
    return _new_year(_hebrew_year(year + 1)).to_greg()


def yom_kippur(year):
    """
    Return the Gregorian date for Yom Kippur in the given Gregorian calendar
    year.
    """
    return _yom_kippur(_hebrew_year(year + 1)).to_greg()


def sukkoth(year):
    """
    Return the Gregorian date for Sukkoth in the given Gregorian calendar year.
    """
    return _sukkoth(_hebrew_year(year + 1)).to_greg()


def simchat_torah(year):
    """
    Return the Gregorian date for Simchat Torah in the given Gregorian calendar
    year.
    """
    return _simchat_torah(_hebrew_year(year + 1)).to_greg()


class _Holiday(Holiday):
    """Holiday that evaluates to no dates if it has no reference dates.

    Use this class in place of `Holiday` to define a holiday that has an observance
    and a `start_date` or an `end_date`. If the holiday's `start_date` or `end_date`
    excludes every reference date, pandas < 2.0 evaluates the observance to an
    `Index` of dtype object, rather than to an empty `DatetimeIndex` as pandas >= 2.0
    does. Filtering that `Index` by `days_of_week` raises an AttributeError.
    """

    # NOTE This class can be removed when the minimum supported version of
    # pandas bumps to 2.0 (pandas 2.0 introduced the behavior defined here to
    # `Holiday._apply_rule`).
    def _apply_rule(self, dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
        if dates.empty:
            return dates.copy()
        return super()._apply_rule(dates)


def _days_from_holiday(
    dt: pd.Timestamp, holiday: Callable[[int], dates.GregorianDate], days: int
) -> pd.Timestamp:
    """Return the date `days` days from `holiday` in the year of `dt`.

    `days` can be positive or negative.
    """
    return pd.Timestamp(holiday(dt.year).to_pydate()) + pd.Timedelta(days=days)


def _observance(
    holiday: Callable[[int], dates.GregorianDate], days: int = 0
) -> Callable[[pd.Timestamp], pd.Timestamp]:
    """Return an observance for a date relative to a holiday.

    Parameters
    ----------
    holiday
        Function that returns the Gregorian date of the holiday in a given
        Gregorian calendar year.
    days
        Number of days from the holiday to the observed date, negative if the
        observed date is before the holiday.

    Returns
    -------
    Callable[[pd.Timestamp], pd.Timestamp]
        Function that receives a date and returns the date that is `days` days
        from the holiday in the year of the received date. Pass the function as
        the `observance` of a `Holiday` that is defined for 1 January.
    """
    return functools.partial(_days_from_holiday, holiday=holiday, days=days)


def _yom_kippur_eve_observed(dt: pd.Timestamp) -> pd.Timestamp:
    """Return the date on which Yom Kippur Eve is observed in the year of `dt`.

    Yom Kippur Eve is observed on the preceding Friday if Yom Kippur Eve falls on a
    Saturday or a Sunday.
    """
    return previous_friday(_days_from_holiday(dt, yom_kippur, -1))


# Holiday instances for holidays observed by TASE.
Purim = Holiday("Purim", month=1, day=1, observance=_observance(purim))
PassoverEve = Holiday(
    "Passover Eve", month=1, day=1, observance=_observance(passover, -1)
)
Passover = Holiday("Passover", month=1, day=1, observance=_observance(passover))
Passover2Eve = Holiday(
    "Passover II Eve", month=1, day=1, observance=_observance(passover, 5)
)
Passover2 = Holiday("Passover II", month=1, day=1, observance=_observance(passover, 6))
PentecostEve = Holiday(
    "Pentecost Eve", month=1, day=1, observance=_observance(pentecost, -1)
)
Pentecost = Holiday("Pentecost", month=1, day=1, observance=_observance(pentecost))
FastDay = Holiday("Tisha B'Av", month=1, day=1, observance=_observance(fast_day))
MemorialDay = Holiday(
    "Memorial Day", month=1, day=1, observance=_observance(memorial_day)
)
IndependenceDay = Holiday(
    "Independence Day", month=1, day=1, observance=_observance(memorial_day, 1)
)
NewYearsEve = Holiday(
    "New Year's Eve", month=1, day=1, observance=_observance(new_year, -1)
)
NewYear = Holiday("New Year", month=1, day=1, observance=_observance(new_year))
NewYear2 = Holiday("New Year II", month=1, day=1, observance=_observance(new_year, 1))
YomKippurEve = Holiday(
    "Yom Kippur Eve", month=1, day=1, observance=_observance(yom_kippur, -1)
)
YomKippurEveObserved = _Holiday(
    "Market Holiday",
    month=1,
    day=1,
    observance=_yom_kippur_eve_observed,
    start_date=pd.Timestamp("2026-01-05"),
)
YomKippur = Holiday("Yom Kippur", month=1, day=1, observance=_observance(yom_kippur))
SukkothEve = Holiday("Sukkoth Eve", month=1, day=1, observance=_observance(sukkoth, -1))
Sukkoth = Holiday("Sukkoth", month=1, day=1, observance=_observance(sukkoth))
SimchatTorahEve = Holiday(
    "Simchat Torah Eve", month=1, day=1, observance=_observance(simchat_torah, -1)
)
SimchatTorah = Holiday(
    "Simchat Torah", month=1, day=1, observance=_observance(simchat_torah)
)

DaysOfWeekBefore2026 = (0, 1, 2, 3, 6)
DaysOfWeek = (0, 1, 2, 3, 4)
StartDate = pd.Timestamp("2026-01-05")
EndDate = pd.Timestamp("2026-01-05")


# Sukkoth interim days - the 3 days following Sukkoth
SukkothInterimDay1 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 1),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
SukkothInterimDay1Before2026 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 1),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
SukkothInterimDay2 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 2),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
SukkothInterimDay2Before2026 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 2),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
SukkothInterimDay3 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 3),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
SukkothInterimDay3Before2026 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 3),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
SukkothInterimDay4 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 4),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
SukkothInterimDay4Before2026 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 4),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
SukkothInterimDay5 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 5),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
SukkothInterimDay5Before2026 = _Holiday(
    "Sukkoth Interim Day",
    month=1,
    day=1,
    observance=_observance(sukkoth, 5),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)

# Passover interim days are the days between beginning and end of passover.
# Any otherwise regular business day in that period becomes an early close day.
PassoverInterimDay1 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 1),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
PassoverInterimDay1Before2026 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 1),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
PassoverInterimDay2 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 2),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
PassoverInterimDay2Before2026 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 2),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
PassoverInterimDay3 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 3),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
PassoverInterimDay3Before2026 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 3),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
PassoverInterimDay4 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 4),
    start_date=StartDate,
    days_of_week=DaysOfWeek,
)
PassoverInterimDay4Before2026 = _Holiday(
    "Passover Interim Day",
    month=1,
    day=1,
    observance=_observance(passover, 4),
    end_date=EndDate,
    days_of_week=DaysOfWeekBefore2026,
)
