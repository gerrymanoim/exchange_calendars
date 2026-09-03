import pandas as pd

from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.offsets import (
    MultipleWeekmaskCustomBusinessDay,
)


def test_weekmask_transition_edge_case():
    """Checks that date ranges across transitions from one weekmask to another work
    correctly in the following scenario: When transitioning from one weekmask period to
    the following, the first business day in the new period, according to the previous
    period's weekmask, is not the first business day in the new period, according to the
    second period.
    """

    # A business day with two weekmask periods. The first business day 2023-07-03 after
    # the last one 2023-06-30 according to the first period is 2023-07-03, but the
    # actual first business day in second period is 2023-07-02.
    bday = MultipleWeekmaskCustomBusinessDay(
        holidays=[],
        calendar=HolidayCalendar(rules=[]),
        weekmask="1111100",
        weekmasks=[
            (None, pd.Timestamp("2023-07-01"), "1111100"),
            (pd.Timestamp("2023-07-02"), None, "0000011"),
        ],
    )

    # Check business days in range around transition point.
    assert pd.date_range(
        pd.Timestamp("2023-06-29"), pd.Timestamp("2023-07-11"), freq=bday
    ).equals(
        pd.DatetimeIndex(
            data=[
                pd.Timestamp("2023-06-29"),
                pd.Timestamp("2023-06-30"),  # Last business day in first period.
                pd.Timestamp("2023-07-02"),  # First business day in second period.
                pd.Timestamp("2023-07-08"),
                pd.Timestamp("2023-07-09"),
            ]
        )
    )
