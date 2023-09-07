from datetime import time
from itertools import chain
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import Holiday

from exchange_calendars.exchange_calendar import ExchangeCalendar, HolidayCalendar

SaudiFoundingDay = Holiday("Saudi Founding Day", month=2, day=22)

NationalDayOfSaudiArabia = Holiday("National Day of Saudi Arabia", month=9, day=23)

EidAlAdhaHoliday = pd.to_datetime(
    [
        "2023-06-27",
        "2023-06-28",
        "2023-06-29",
        "2023-06-30",
        "2023-07-01",
        "2023-07-02",
        "2022-07-07",
        "2022-07-08",
        "2022-07-09",
        "2022-07-10",
        "2022-07-11",
        "2022-07-12",
        "2022-07-13",
        "2021-07-16",
        "2021-07-17",
        "2021-07-18",
        "2021-07-19",
        "2021-07-20",
        "2021-07-21",
        "2021-07-22",
    ]
)

EidAlFiterHoliday = pd.to_datetime(
    [
        "2023-04-18",
        "2023-04-19",
        "2023-04-20",
        "2023-04-21",
        "2023-04-22",
        "2023-04-23",
        "2023-04-24",
        "2023-04-25",
        "2022-04-28",
        "2022-04-29",
        "2022-04-30",
        "2022-05-01",
        "2022-05-02",
        "2022-05-03",
        "2022-05-04",
        "2022-05-05",
        "2022-05-06",
        "2022-05-07",
        "2022-05-08",
        "2021-05-13",
        "2021-05-14",
        "2021-05-15",
        "2021-05-16",
    ]
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

    def _bound_min_error_msg(self, start: pd.Timestamp) -> str:
        msg = super()._bound_min_error_msg(start)
        return (
            msg
            + f"(The exchange {self.name} does not have complete holidays prior to 2021.)"
        )

    @classmethod
    def bound_max(cls) -> pd.Timestamp:
        return pd.Timestamp("2023-12-31")

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
