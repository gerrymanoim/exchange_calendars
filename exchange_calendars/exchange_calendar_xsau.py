from datetime import time
from itertools import chain
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import Holiday
import numpy as np  # for concatenate

from exchange_calendars.exchange_calendar import ExchangeCalendar, HolidayCalendar

SaudiFoundingDay = Holiday("Saudi Founding Day", month=2, day=22)

NationalDayOfSaudiArabia = Holiday("National Day of Saudi Arabia", month=9, day=23)

# https://www.saudiexchange.sa/wps/portal/saudiexchange/about-saudi-exchange/exchange-media-centre/saudi-exchange-holiday-calendar?locale=en
EidAlAdhaHoliday = pd.to_datetime(
    np.concatenate(
        [
            pd.date_range("2029-04-20", "2029-04-28"),
            pd.date_range("2028-05-03", "2028-05-09"),
            pd.date_range("2027-05-14", "2027-05-22"),
            pd.date_range("2026-05-22", "2026-05-30"),
            pd.date_range("2025-06-04", "2025-06-09"),
            pd.date_range("2024-06-13", "2024-06-23"),
            pd.date_range("2023-06-27", "2023-07-02"),
            pd.date_range("2022-07-07", "2022-07-13"),
            pd.date_range("2021-07-16", "2021-07-22"),
        ]
    )
)

EidAlFiterHoliday = pd.to_datetime(
    np.concatenate(
        [
            pd.date_range("2029-02-12", "2029-02-18"),
            pd.date_range("2028-02-25", "2028-03-04"),
            pd.date_range("2027-03-05", "2027-03-13"),
            pd.date_range("2026-03-17", "2026-03-23"),
            pd.date_range("2025-03-27", "2025-04-02"),
            pd.date_range("2024-04-05", "2024-04-15"),
            pd.date_range("2023-04-18", "2023-04-25"),
            pd.date_range("2022-04-28", "2022-05-08"),
            pd.date_range("2021-05-13", "2021-05-16"),
        ]
    )
)


class XSAUExchangeCalendar(ExchangeCalendar):
    """
    Exchange calendar for the Saudi Exchange (XSAU)
    Available here: https://www.saudiexchange.sa/wps/portal/saudiexchange/rules-guidance/capital-market-overview/trading-cycle-and-times
    """

    name = "XSAU"

    tz = ZoneInfo("Asia/Riyadh")

    open_times = ((None, time(10)),)

    close_times = ((None, time(15)),)

    @classmethod
    def bound_min(cls) -> pd.Timestamp:
        return pd.Timestamp("2021-01-01")

    @classmethod
    def bound_max(cls) -> pd.Timestamp:
        return pd.Timestamp("2029-12-31")

    @property
    def regular_holidays(self):
        return HolidayCalendar([SaudiFoundingDay, NationalDayOfSaudiArabia])

    @property
    def weekmask(self):
        return "1111001"

    @property
    def adhoc_holidays(self):
        return list(chain(EidAlAdhaHoliday, EidAlFiterHoliday))
