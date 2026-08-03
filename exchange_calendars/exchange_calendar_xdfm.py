from datetime import time
from itertools import chain
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import Holiday

from exchange_calendars.exchange_calendar import ExchangeCalendar, HolidayCalendar

# New Year's Day is observed as a trading holiday every year.
# https://assets.dfm.ae/docs/default-source/circulars/circular-12-2025-trading-and-settlementholidays-for-the-calendar-year-2026-for-securities-market-excluding-derivatives-contracts-english.pdf
NewYearsDay = Holiday("New Year's Day", month=1, day=1)

# UAE National Day is a two-day holiday (2 and 3 December) observed every
# year, per DFM's annual "Trading and Settlement Holidays" circulars (see
# citations on adhoc holidays below for individual years).
UAENationalDayDay1 = Holiday("UAE National Day (Day 1)", month=12, day=2)
UAENationalDayDay2 = Holiday("UAE National Day (Day 2)", month=12, day=3)

# Commemoration Day (1 December) was observed as an additional DFM trading
# holiday in 2022 and 2023 but has not appeared in DFM's published holiday
# circulars for 2024, 2025 or 2026 (including years where 1 December fell on
# a weekday), so it is not treated as a recurring regular holiday and is
# instead listed, for the years it was observed, as an ad-hoc holiday below.

# Islamic holidays shift each year with the lunar Hijri calendar and are
# sourced from DFM's (and, for 2022, Nasdaq Dubai's, which outsources AED
# equity trading to DFM) officially published annual holiday circulars.
# Only weekday closures are listed below; dates that fall on the Sat/Sun
# weekend are already excluded by the weekmask and are omitted.
#
# 2022 (Nasdaq Dubai Circular No: 65/2021, "AED Trading Holidays and
# Settlement Calendar 2022", https://a.storyblok.com/f/81548/x/9a08d5cd65/
# circular-65-nd-aed-settlement-calendar-2022.pdf):
#   Eid Al Fitr: 2-3 May 2022; Eid Al Adha: 11 Jul 2022;
#   Commemoration Day: 1 Dec 2022; UAE National Day: 2 Dec 2022
#   (3 Dec 2022 fell on the Saturday weekend).
#
# 2023 (DFM Circular No: DClear/2022/14, "Trading and Settlement Holidays
# for the Calendar Year 2023",
# https://api.dfm.ae/docs/default-source/dubai-clear/circulars/
# holiday-calendar-2023---securities-market.pdf):
#   Eid Al Fitr: 20-21 Apr 2023; Arafah (Haj) Day / Eid Al Adha:
#   27-29 Jun 2023; Hijri New Year: 19 Jul 2023; Prophet Muhammad's
#   Birthday: 27 Sep 2023; Commemoration Day: 1 Dec 2023
#   (2-3 Dec 2023 fell on the Sat/Sun weekend).
#
# 2024 (DFM Circular No: 15/2023, "Trading and Settlement Holidays for the
# Calendar Year 2024 for Securities Market (Excluding Derivatives
# contracts)"):
#   Eid Al Fitr: 10-12 Apr 2024; Eid Al Adha: 17-19 Jun 2024
#   (Arafah Day, 16 Jun 2024, fell on the Sunday weekend, as did Hijri New
#   Year, 7 Jul 2024, and Prophet's Birthday, 15 Sep 2024).
#
# 2025 (DFM Circular No: 06/2024, "Trading and Settlement Holidays for the
# Calendar Year 2025 for Securities Market (Excluding Derivatives
# contracts)",
# https://assets.dfm.ae/docs/default-source/circulars/06_2024_trading-and-
# settlementholidays-for-the-calendar-year-2025-for-securities-market-
# (excluding-derivatives-contracts)-english.pdf):
#   Eid Al Fitr: 31 Mar - 1 Apr 2025 (30 Mar 2025 fell on the Sunday
#   weekend); Arafah (Haj) Day: 5 Jun 2025; Eid Al Adha: 6 Jun 2025
#   (7 Jun 2025 fell on the Saturday weekend); Hijri New Year: 26 Jun 2025;
#   Prophet Mohammed's Birthday: 4 Sep 2025.
#
# 2026 (DFM Circular No: 12/2025, "Trading and Settlement Holidays for the
# Calendar Year 2026 for Securities Market (Excluding Derivatives
# contracts)",
# https://assets.dfm.ae/docs/default-source/circulars/circular-12-2025-
# trading-and-settlementholidays-for-the-calendar-year-2026-for-securities-
# market-excluding-derivatives-contracts-english.pdf):
#   Eid Al Fitr: 19-20 Mar 2026 (21 Mar 2026 fell on the Saturday weekend);
#   Arafah (Haj) Day: 26 May 2026; Eid Al Adha: 27-29 May 2026; Hijri New
#   Year: 16 Jun 2026; Prophet Muhammad's Birthday: 25 Aug 2026.
#
# Islamic holidays are tentative and subject to change by DFM circular; this
# list should be extended in step with DFM's future annual circulars as
# `bound_max` is pushed forward.
AdHocHolidays = pd.to_datetime(
    [
        # 2022
        "2022-05-02",
        "2022-05-03",
        "2022-07-11",
        "2022-12-01",
        "2022-12-02",
        # 2023
        "2023-04-20",
        "2023-04-21",
        "2023-06-27",
        "2023-06-28",
        "2023-06-29",
        "2023-07-19",
        "2023-09-27",
        "2023-12-01",
        # 2024
        "2024-04-10",
        "2024-04-11",
        "2024-04-12",
        "2024-06-17",
        "2024-06-18",
        "2024-06-19",
        # 2025
        "2025-03-31",
        "2025-04-01",
        "2025-06-05",
        "2025-06-06",
        "2025-06-26",
        "2025-09-04",
        # 2026
        "2026-03-19",
        "2026-03-20",
        "2026-05-26",
        "2026-05-27",
        "2026-05-28",
        "2026-05-29",
        "2026-06-16",
        "2026-08-25",
    ]
)


class XDFMExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Dubai Financial Market (XDFM)

    DFM moved its trading week from Sunday-Thursday to Monday-Friday, and
    its continuous trading session to 10:00-15:00 local time, effective
    3 January 2022, in step with the UAE's shift of its official weekend
    from Friday-Saturday to Saturday-Sunday. The calendar is bounded at
    that date (in the same fashion that XSAUExchangeCalendar is bounded at
    the analogous 2021 change in Saudi Arabia) to avoid modelling the
    pre-2022 Sunday-Thursday week.
    https://www.thenationalnews.com/business/markets/2021/12/08/dubais-dfm-to-shift-trading-hours-from-monday-to-friday/
    https://gulfnews.com/business/markets/uae-weekend-change-stock-markets-to-operate-from-monday-to-friday-starting-next-year-1.84253633

    Available here: https://www.dfm.ae/
    """

    name = "XDFM"

    tz = ZoneInfo("Asia/Dubai")

    open_times = ((None, time(10)),)

    close_times = ((None, time(15)),)

    @classmethod
    def bound_min(cls) -> pd.Timestamp:
        return pd.Timestamp("2022-01-03")

    @classmethod
    def bound_max(cls) -> pd.Timestamp:
        return pd.Timestamp("2026-12-31")

    @property
    def regular_holidays(self):
        return HolidayCalendar([NewYearsDay, UAENationalDayDay1, UAENationalDayDay2])

    @property
    def weekmask(self):
        return "1111100"

    @property
    def adhoc_holidays(self):
        return list(chain(AdHocHolidays))
