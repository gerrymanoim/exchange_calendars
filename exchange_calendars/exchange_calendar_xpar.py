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
    boxing_day,
    christmas,
    christmas_eve,
    european_labour_day,
    new_years_day,
    new_years_eve,
    whit_monday,
)
from .exchange_calendar import WEEKDAYS, HolidayCalendar, ExchangeCalendar

# Sources for the historical holiday regime (SBF-Paris Bourse and Euronext
# Paris notices, releases and statistics, as archived by the Internet
# Archive):
#   [1] SBF release of 3 January 1997, market activity in December 1996: 21
#       sessions (3,241,014 trades at a daily average of 154,334), least
#       active session 26 December
#       http://web.archive.org/web/19970722161132/http://www.bourse-de-paris.fr:80/Bourse/sbf/NEWS/Communiques/activ3-01-fr.html
#   [2] SBF monthly letter Bours'Info no. 13 (March 1998), 22 sessions in
#       December 1997
#       http://web.archive.org/web/20031102195258/http://www.bourse-de-paris.fr:80/fr/tools0/pdf/archives/1998/BI_3-98.pdf
#   [3] SBF notice 97-4108 (12.12.1997), market calendar 1998
#       http://web.archive.org/web/19980711051740/http://www.bourse-de-paris.fr:80/bourse/sbf/euro/fr/eurovous/ferm98.pdf
#   [4] SBF notice 99-1320 (08.04.1999), markets closed on 31 December 1999
#       http://web.archive.org/web/20000303185130/http://www.bourse-de-paris.fr:80/fr/tools0/pdf/news/ferm311299.pdf
#   [5] SBF notice 99-4312 (05.10.1999), market calendar 2000
#       http://web.archive.org/web/20030621200919/http://www.bourse-de-paris.fr:80/fr/tools0/pdf/market/a/cal2000pbsa.pdf
#   [6] Euronext Paris notice 2000-4660 (07.11.2000), market calendar 2001
#       http://web.archive.org/web/20010211192905/http://customerservice.euronext.fr:80/vf/pages/News/Calendrier/calendrier.htm
#   [7] Euronext Fact Book 2001, calendar of business days in 2002
#       http://web.archive.org/web/20030426024844/http://www.bourse-de-paris.fr:80/centredoc/pdf/factbook_euronext_2001.pdf
NewYearsDay = new_years_day()

WhitMonday = whit_monday(end_date="2002")

LabourDay = european_labour_day()

BastilleDay = Holiday(
    "Bastille Day",
    month=7,
    day=14,
    end_date="2002",
)

# Christmas Eve was a session in 1996 and 1997 [1][2] and an exchange
# holiday in 1998 [3]. It is kept as an early close in every other year; the
# closing time before 2002 is not established by the sources above.
ChristmasEveUntil1997 = christmas_eve(end_date="1997-12-31", days_of_week=WEEKDAYS)
ChristmasEveFrom1999 = christmas_eve(start_date="1999-01-01", days_of_week=WEEKDAYS)

Christmas = christmas()

# Boxing Day was a trading day in 1996 and 1997 [1][2] and is an exchange
# holiday from 2000 [5][6][7] (26 December 1998 and 1999 fell on a weekend).
BoxingDayUntil1995 = boxing_day(end_date="1995-12-31")
BoxingDayFrom2000 = boxing_day(start_date="2000-01-01")

# New Year's Eve was a trading day in 1996 and 1997 [1][2] and an exchange
# holiday from 1998 through 2001 [3][4][6]. It is an early close from 2002 [7].
# No source was found for the years before 1996, so the rules for Boxing Day
# and New Year's Eve are left unchanged there.
NewYearsEveUntil1995 = new_years_eve(end_date="1995-12-31")
NewYearsEve1998To2001 = new_years_eve(start_date="1998-01-01", end_date="2002")
NewYearsEveInOrAfter2002 = new_years_eve(
    start_date="2002",
    days_of_week=WEEKDAYS,
)

# Ad-hoc Holidays
# ---------------
# Before Euronext harmonised its calendar, the Paris Bourse also closed on
# French public holidays. The 1998 market calendar [3] lists these closures
# in addition to the regular holidays above.
VictoryDay1998 = Timestamp("1998-05-08")
AscensionDay1998 = Timestamp("1998-05-21")
BridgeDay1998 = Timestamp("1998-07-13")  # "fermeture collective de la Place"
ArmisticeDay1998 = Timestamp("1998-11-11")
ChristmasEve1998 = Timestamp("1998-12-24")


class XPARExchangeCalendar(ExchangeCalendar):
    """
    Calendar for the Euronext Paris exchange, and the primary calendar for the
    country of France.

    Open Time: 9:00 AM, CET (Central European Time)
    Close Time: 5:30 PM, CET (Central European Time)

    Regularly-Observed Holidays:
      - New Year's Day
      - Good Friday
      - Easter Monday
      - Whit Monday (until 2001)
      - Labour Day
      - Bastille Day (until 2001)
      - Christmas Day
      - Boxing Day (not observed 1996 and 1997)
      - New Year's Eve (until 2001, not observed 1996 and 1997)

    Early Closes:
      - Christmas Eve (holiday in 1998)
      - New Year's Eve (from 2002)

    Ad-hoc Holidays:
      - 1998: Victory Day, Ascension Day, 13 July, Armistice Day and
        Christmas Eve

    Other countries on the Euronext:
      - Belgium
      - Netherlands
      - Portugal
    """

    # Source: https://www.euronext.com/en/calendars-hours
    regular_early_close = time(14, 5)

    name = "XPAR"  # Euronext Paris
    tz = ZoneInfo("Europe/Paris")
    open_times = ((None, time(9)),)
    close_times = ((None, time(17, 30)),)

    @property
    def regular_holidays(self):
        return HolidayCalendar(
            [
                NewYearsDay,
                GoodFriday,
                EasterMonday,
                WhitMonday,
                LabourDay,
                BastilleDay,
                Christmas,
                BoxingDayUntil1995,
                BoxingDayFrom2000,
                NewYearsEveUntil1995,
                NewYearsEve1998To2001,
            ]
        )

    @property
    def adhoc_holidays(self):
        return [
            VictoryDay1998,
            AscensionDay1998,
            BridgeDay1998,
            ArmisticeDay1998,
            ChristmasEve1998,
        ]

    @property
    def special_closes(self):
        return [
            (
                self.regular_early_close,
                HolidayCalendar(
                    [
                        ChristmasEveUntil1997,
                        ChristmasEveFrom1999,
                        NewYearsEveInOrAfter2002,
                    ]
                ),
            ),
        ]
