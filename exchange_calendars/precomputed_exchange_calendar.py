from __future__ import annotations
from abc import abstractmethod

import numpy as np
import pandas as pd

from .exchange_calendar import ExchangeCalendar


class PrecomputedExchangeCalendar(ExchangeCalendar):
    """
    Used to model an exchange calendar whose holidays inlcude holidays that
    are precomputed and hardcoded.
    """

    @abstractmethod
    def precomputed_holidays(cls) -> pd.DatetimeIndex | list[pd.Timestamp]:
        """Precomputed holidays.

        Subclass should implement as a classmethod.
        """
        raise NotImplementedError()

    @property
    def adhoc_holidays(self) -> pd.DatetimeIndex | list[pd.Timestamp]:
        return self.precomputed_holidays()

    @classmethod
    def _earliest_precomputed_year(cls) -> int:
        return np.min(cls.precomputed_holidays()).year

    @classmethod
    def _latest_precomputed_year(cls) -> int:
        return np.max(cls.precomputed_holidays()).year

    @classmethod
    def bound_min(cls) -> pd.Timestamp:
        return pd.Timestamp(f"{cls._earliest_precomputed_year()}-01-01")

    @classmethod
    def bound_max(cls) -> pd.Timestamp:
        return pd.Timestamp(f"{cls._latest_precomputed_year()}-12-31")

    def _bound_min_error_msg(self, start: pd.Timestamp) -> str:
        return (
            f"The {self.name} holidays are only recorded back to the year"
            f" {self._earliest_precomputed_year()}, cannot instantiate the"
            f" {self.name} calendar from {start}."
        )

    def _bound_max_error_msg(self, end: pd.Timestamp) -> str:
        return (
            f"The {self.name} holidays are only recorded to the year"
            f" {self._latest_precomputed_year()}, cannot instantiate the"
            f" {self.name} calendar through to {end}."
        )
