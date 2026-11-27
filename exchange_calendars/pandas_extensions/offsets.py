# https://github.com/pandas-dev/pandas/blob/master/pandas/tseries/offsets.py
# https://github.com/pandas-dev/pandas/blob/master/pandas/_libs/tslibs/offsets.pyx

from datetime import date, datetime

import pandas as pd
from dateutil.easter import EASTER_ORTHODOX, easter
from pandas._libs.tslibs.conversion import localize_pydatetime
from pandas._libs.tslibs.offsets import apply_wraps
from pandas.tseries.offsets import BaseOffset


def _is_normalized(dt):
    if dt.hour != 0 or dt.minute != 0 or dt.second != 0 or dt.microsecond != 0:
        # Regardless of whether dt is datetime vs Timestamp
        return False
    if isinstance(dt, pd.Timestamp):
        return dt.nanosecond == 0
    return True


class SingleConstructorOffset(BaseOffset):
    def __reduce__(self): ...


class OrthodoxEaster(SingleConstructorOffset):
    """
    DateOffset for the Orthodox Easter holiday.
    """

    def __setstate__(self, state):
        self.n = state.pop("n")
        self.normalize = state.pop("normalize")

    @apply_wraps
    def _apply(self, other: datetime) -> datetime:
        current_easter = easter(other.year, method=EASTER_ORTHODOX)
        current_easter = datetime(
            current_easter.year, current_easter.month, current_easter.day
        )
        current_easter = localize_pydatetime(current_easter, other.tzinfo)

        n = self.n
        if n >= 0 and other < current_easter:
            n -= 1
        elif n < 0 and other > current_easter:
            n += 1

        new = easter(other.year + n, method=EASTER_ORTHODOX)
        return datetime(
            new.year,
            new.month,
            new.day,
            other.hour,
            other.minute,
            other.second,
            other.microsecond,
        )

    def is_on_offset(self, dt: datetime) -> bool:
        if self.normalize and not _is_normalized(dt):
            return False

        return date(dt.year, dt.month, dt.day) == easter(
            dt.year, method=EASTER_ORTHODOX
        )
