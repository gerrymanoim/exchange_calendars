#
# Copyright 2018 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import time
from zoneinfo import ZoneInfo

from pandas import Timestamp
from pandas.tseries.holiday import EasterMonday, GoodFriday, Holiday

from .common_holidays import (
    ascension_day,
    boxing_day,
    christmas,
    christmas_eve,
    european_labour_day,
    new_years_day,
    new_years_eve,
    whit_monday,
)
from .exchange_calendar import HolidayCalendar, ExchangeCalendar

# Regular Holidays
# ----------------
# Sources for the historical holiday regime (SWX Swiss Exchange notices and
# trading calendars, as archived by the Internet Archive):
#   [1] SWX message 72/99 (11.10.1999), trading calendar 1999/2000
#       http://web.archive.org/web/2005/http://www.swx.com/swx_messages/1999/swx7299_calendar.pdf
#   [2] SWX messages 71/2000 (27.09.2000) and 90/2000 (29.11.2000), trading
#       calendar 2000/2001
#       http://web.archive.org/web/2006/http://www.swx.com/swx_messages/2000/swx9000_calendar.pdf
#   [3] SWX message 44/2001 (15.05.2001), trading calendar effective 25 June
#       2001: 2 January, Ascension Day, Whit Monday and 1 August are trading
#       days for equities (closed for fixed income only)
#       http://web.archive.org/web/2006/http://www.swx.com/swx_messages/2001/swx4401e.pdf
#   [4] SWX message 107/2001 (19.11.2001), 24.12.2001 not a trading day
#       http://web.archive.org/web/2006/http://www.swx.com/swx_messages/2001/swx10701e.pdf
#   [5] SWX trading calendar 2001/2002
#       http://web.archive.org/web/2003/http://www.swx.com/market/tradcal2002.pdf
#   [6] SWX message 56/2002 (10.07.2002), 24 and 31 December 2002 and
#       2 January 2003 closed
#       http://web.archive.org/web/2006/http://www.swx.com/swx_messages/2002/swx5602e.pdf
#   [7] SWX message 09/2003 (20.02.2003), Ascension Day and Whit Monday are
#       exchange holidays "in future"; 1 August remains a trading day
#       http://web.archive.org/web/2006/http://www.swx.com/swx_messages/2003/swx0903e.pdf
#   [8] SWX trading calendar 2002/2003
#       http://web.archive.org/web/2003/http://www.swx.com/market/tradcal2003.pdf
#   [9] SWX message 58/2003 (30.07.2003), 24 and 31 December 2003 and
#       2 January 2004 closed
#       http://web.archive.org/web/2004/http://www.swx.com/swx_messages/2003/swx5803d.pdf
#   [10] SWX message 51/2004 (26.08.2004), 24 and 31 December 2004 closed
#       http://web.archive.org/web/2006/http://www.swx.com/swx_messages/2004/swx5104e.pdf
#   [11] SWX trading calendar 2005 (1 August 2005 closed for fixed income only)
#       http://web.archive.org/web/2005/http://www.swx.com/download/trading/information/trading_calendar/calendar_2005.pdf
#   [12] SWX trading calendar 2006 (1 August 2006 a market holiday)
#       http://web.archive.org/web/20060324041803/http://www.swx.com/trading/information/calendar/2006/grid_en.html
#   [13] SWX message 09/2006 (16.02.2006), holidays that "will generally
#       apply": 1 and 2 January, Good Friday, Easter Monday, 1 May, Ascension
#       Day, Whit Monday, 1 August, 25 and 26 December
#       http://web.archive.org/web/20060720021640/http://www.swx.com/swx_messages/2006/swx0906e.pdf
#   [14] SIX Swiss Exchange daily price history of SIX-listed shares, as
#       published by SIX (from 15 December 1997): traded volume on
#       24 and 31 December 1997; no bar on 24 or 31 December 1998
#       https://www.six-group.com/en/market-data/shares.html
#   [15] Daily bars of an independent commercial data vendor: traded volume
#       on 24 and 31 December 1996
NewYearsDay = new_years_day()

# Berchtold's Day was a trading day in 2002 only [3][4][5]. It was closed in
# 2001 [2] and from 2003 [6][8][9].
BerchtoldsDayUntil2001 = Holiday(
    "Berchtold's Day",
    month=1,
    day=2,
    end_date="2001-12-31",
)

BerchtoldsDayFrom2003 = Holiday(
    "Berchtold's Day",
    month=1,
    day=2,
    start_date="2003-01-01",
)

EuropeanLabourDay = european_labour_day()

# Ascension Day and Whit Monday were trading days in 2002 only [3][5]. Both
# were closed in 2000 and 2001 [1][2] and from 2003 [7][8].
AscensionDayUntil2001 = ascension_day(end_date="2001-12-31")

AscensionDayFrom2003 = ascension_day(start_date="2003-01-01")

WhitMondayUntil2001 = whit_monday(end_date="2001-12-31")

WhitMondayFrom2003 = whit_monday(start_date="2003-01-01")

# Swiss National Day was closed in 2000 [1][2], a trading day from 2001
# through 2005 [3][5][7][8][11] and closed again from 2006 [12][13].
SwissNationalDayUntil2000 = Holiday(
    "Swiss National Day",
    month=8,
    day=1,
    end_date="2000-12-31",
)

SwissNationalDayFrom2006 = Holiday(
    "Swiss National Day",
    month=8,
    day=1,
    start_date="2006-01-01",
)

# Christmas Eve and New Year's Eve were trading days in 1996 [15] and 1997
# [14] and closed from 1998 [1][14]. No evidence was found for the years before
# 1996, which keep both days as holidays.
ChristmasEveUntil1995 = christmas_eve(end_date="1995-12-31")

ChristmasEveFrom1998 = christmas_eve(start_date="1998-01-01")

Christmas = christmas()

BoxingDay = boxing_day()

NewYearsEveUntil1995 = new_years_eve(end_date="1995-12-31")

NewYearsEveFrom1998 = new_years_eve(start_date="1998-01-01")

# Ad-hoc Holidays
# ---------------
# Monday 3 January 2000 was an exchange holiday ("customer holiday") for the
# year 2000 changeover [1].
Y2KCustomerHoliday = Timestamp("2000-01-03")


class XSWXExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Swiss Exchange (XSWX)

    Open Time: 8:00 AM, CET, CEST in summer
    Close Time: 5:30 PM, CET, CEST in summer

    Regularly-Observed Holidays:
    - New Year's Day
    - Berchtold's Day (not observed in 2002)
    - Good Friday
    - Easter Monday
    - Labour Day
    - Ascension Day (not observed in 2002)
    - Whit Monday (not observed in 2002)
    - Swiss National Day (not observed 2001 through 2005)
    - Christmas Eve (not observed in 1996 and 1997)
    - Christmas Day
    - Boxing Day
    - New Year's Eve (not observed in 1996 and 1997)

    Ad-hoc Holidays:
    - 3 January 2000 (year 2000 changeover)
    """

    name = "XSWX"

    tz = ZoneInfo("Europe/Zurich")

    open_times = ((None, time(9, 0)),)

    close_times = ((None, time(17, 30)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                BerchtoldsDayUntil2001,
                BerchtoldsDayFrom2003,
                EasterMonday,
                GoodFriday,
                EuropeanLabourDay,
                AscensionDayUntil2001,
                AscensionDayFrom2003,
                WhitMondayUntil2001,
                WhitMondayFrom2003,
                SwissNationalDayUntil2000,
                SwissNationalDayFrom2006,
                ChristmasEveUntil1995,
                ChristmasEveFrom1998,
                Christmas,
                BoxingDay,
                NewYearsEveUntil1995,
                NewYearsEveFrom1998,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [Y2KCustomerHoliday]
