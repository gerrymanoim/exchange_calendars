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
EidAlAdhaHoliday = pd.to_datetime(np.concatenate(
    [
        pd.date_range('2024-06-13', '2024-06-23'),
        pd.date_range('2023-06-27', '2023-07-02'),
        pd.date_range('2022-07-07', '2022-07-13'),
        pd.date_range('2021-07-16', '2021-07-22')
    ]))

EidAlFiterHoliday = pd.to_datetime(np.concatenate(
    [
        pd.date_range('2024-04-05', '2024-04-15'),
        pd.date_range('2023-04-18', '2023-04-25'),
        pd.date_range('2022-04-28', '2022-05-08'),
        pd.date_range('2021-05-13', '2021-05-16')
    ]))


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

    def _bound_min_error_msg(self, start: pd.Timestamp) -> str:
        msg = super()._bound_min_error_msg(start)
        return (
            msg
            + f"(The exchange {self.name} does not have complete holidays prior to 2021.)"
        )

    @classmethod
    def bound_max(cls) -> pd.Timestamp:
        return pd.Timestamp("2024-12-31")

    def _bound_max_error_msg(self, end: pd.Timestamp) -> str:
        msg = super()._bound_min_error_msg(end)
        return (
            msg
            + f"(The exchange {self.name} does not have complete holidays beyond 2023.)"
        )

    @property
    def regular_holidays(self):
        return HolidayCalendar([SaudiFoundingDay, NationalDayOfSaudiArabia])

    @property
    def weekmask(self):
        return "1111001"

    @property
    def adhoc_holidays(self):
        return list(chain(EidAlAdhaHoliday, EidAlFiterHoliday))
