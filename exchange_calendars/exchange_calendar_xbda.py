from datetime import time, datetime
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import (
    MO,
    TH,
    FR,
    SA,
    DateOffset,
    Holiday,
    GoodFriday,
    next_monday,
    next_monday_or_tuesday,
    previous_friday,
    weekend_to_monday,
)
from .common_holidays import (
    new_years_day,
    christmas_eve,
    christmas,
    boxing_day,
)
from .exchange_calendar import ExchangeCalendar, HolidayCalendar


def bermuda_day_observance(dt: datetime) -> datetime | None:
    """
    How Bermuda Day is observed.
    """
    if dt.year <= 2017 or dt.year == 2019:
        # For 2017 and before, Bermuda Day was on May 24th.
        dt = next_monday(datetime(dt.year, 5, 24))
    elif dt.year <= 2020:
        # For 2020 and before, it was the last Friday in May.
        dt = dt + DateOffset(weekday=FR(-1))
    else:
        # For 2021 and after, it is the Friday before the last Monday in May.
        dt = dt + DateOffset(weekday=MO(-1)) + DateOffset(weekday=FR(-1))
    return dt


def national_heroes_day_observance(dt: datetime) -> datetime | None:
    """
    How National Heroes Day is observed.
    """
    if dt.year == 2008:
        dt = datetime(2008, 10, 13)
    elif dt.year >= 2009:
        dt = dt + DateOffset(weekday=MO(3))
    else:
        dt = None
    return dt


def queens_birthday_observance(dt: datetime) -> datetime | None:
    """
    How Queens Birthday is observed.
    """
    if dt.year <= 1999:
        # For 1999 and before, it was the 3rd Monday in June.
        dt = dt + DateOffset(weekday=MO(3))
    elif dt.year <= 2008:
        # For 2000 to 2008, it is the Monday after the second Saturday in June.
        dt = dt + DateOffset(weekday=SA(2)) + DateOffset(days=2)
    else:
        dt = None
    return dt


NewYearsDay = new_years_day(observance=weekend_to_monday)
ChristmasEve = christmas_eve(observance=previous_friday)
Christmas = christmas(observance=next_monday)
BoxingDay = boxing_day(observance=next_monday_or_tuesday)


# Bermuda Day: the Friday before the last Monday in May.
BermudaDay = Holiday(
    "Bermuda Day",
    month=5,
    day=31,
    observance=bermuda_day_observance,
)

# National Heroes Day: third Monday in June. Replaced Queens Birthday holiday in 2018.
NationalHeroesDay = Holiday(
    "National Heroes Day",
    month=6,
    day=1,
    observance=national_heroes_day_observance,
    start_date=pd.Timestamp("2018-01-01"),
)

QueensBirthday = Holiday(
    "Queens Birthday",
    month=6,
    day=1,
    observance=queens_birthday_observance,
    end_date=pd.Timestamp("2008-12-31"),
)

# Emancipation Day: Thursday before the first Monday in August.
EmancipationDay = Holiday(
    "Emancipation Day",
    month=8,
    day=1,
    offset=[DateOffset(weekday=MO(1)), DateOffset(weekday=TH(-1))],
    start_date=pd.Timestamp("2000-01-01"),
)

# Cup Match Day: Thursday before the first Monday in August. Cup Match was
# renamed to Emancipation Day from 2000.
CupMatchDay = Holiday(
    "Cup Match Day",
    month=8,
    day=1,
    offset=[DateOffset(weekday=MO(1)), DateOffset(weekday=TH(-1))],
    end_date=pd.Timestamp("1999-12-31"),
)

# Mary Prince Day: Friday after Emancipation Day.
MaryPrinceDay = Holiday(
    "Mary Prince Day",
    month=8,
    day=1,
    offset=[DateOffset(weekday=MO(1)), DateOffset(weekday=TH(-1)), DateOffset(days=1)],
    start_date=pd.Timestamp("2020-01-01"),
)

# Somers Day: Friday after Emancipation Day. Somers Day was renamed to Mary
# Prince Day from 2020.
SomersDay = Holiday(
    "Somers Day",
    month=8,
    day=1,
    offset=[DateOffset(weekday=MO(1)), DateOffset(weekday=TH(-1)), DateOffset(days=1)],
    end_date=pd.Timestamp("2019-12-31"),
)

LabourDay = Holiday(
    "Labour Day",
    month=9,
    day=1,
    offset=DateOffset(weekday=MO(1)),
)

RemembranceDay = Holiday(
    "Remembrance Day",
    month=11,
    day=11,
    observance=weekend_to_monday,
)


class XBDAExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Bermuda Stock Exchange (MIC: XBDA).
    https://www.bsx.com/trading-hours-and-holidays

    Open Time: 9:00 AM, Atlantic/Bermuda
    Close Time: 4:30 PM, Atlantic/Bermuda

    Regularly-Observed Holidays:
      - New Year's Day
      - Good Friday
      - Bermuda Day (the Friday before the last Monday in May)
      - National Heroes Day (third Monday in June)
      - Emancipation Day (Thursday before first Monday in August)
      - Mary Prince Day (Friday after Emancipation Day)
      - Labour Day (first Monday in September)
      - Remembrance Day (November 11, or the following Monday if it falls on a weekend)
      - Christmas Day
      - Boxing Day
    """

    name = "XBDA"
    tz = ZoneInfo("Atlantic/Bermuda")
    open_times = ((None, time(9, 0)),)
    close_times = ((None, time(16, 30)),)
    regular_early_close = time(14, 0)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                BermudaDay,
                NationalHeroesDay,
                QueensBirthday,
                EmancipationDay,
                CupMatchDay,
                MaryPrinceDay,
                SomersDay,
                LabourDay,
                RemembranceDay,
                Christmas,
                BoxingDay,
            ]
        )

    @property
    def special_closes(self):
        return [
            (
                self.regular_early_close,
                HolidayCalendar(
                    [
                        ChristmasEve,
                    ]
                ),
            ),
        ]

    @property
    def adhoc_holidays(self):
        return [
            # Coronation of King Charles III
            pd.Timestamp("2023-05-08"),
            # Queen Elizabeth II Funeral
            pd.Timestamp("2022-09-19"),
            # Flora Duffy Day
            pd.Timestamp("2021-10-18"),
            # Portuguese Welcome 170th Anniversary
            pd.Timestamp("2019-11-04"),
            # Public Holiday
            pd.Timestamp("2007-01-05"),
        ]
