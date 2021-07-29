"""
This script can be used to generate the CSV files used in the exchange calendar
tests. The CSVs include a calendar's sessions, open times, and close times.

This script can be run from the root of the repository with:
    $ python etc/make_exchange_calendar_test_csv.py <calendar_iso_code>
"""
import sys
from os.path import abspath, dirname, join, normpath

import pandas as pd

from exchange_calendars import get_calendar

cal_name = sys.argv[1]
cal = get_calendar(cal_name.upper())

df = pd.DataFrame(
    list(zip(cal.opens, cal.closes, cal.break_starts, cal.break_ends)),
    columns=["market_open", "market_close", "break_start", "break_end"],
    index=cal.closes.index,
)

destination = normpath(
    join(
        abspath(dirname(__file__)),
        "../tests/resources/{}.csv".format(cal_name.lower()),
    ),
)
print("Writing test CSV file to {}".format(destination))

df.to_csv(destination, date_format="%Y-%m-%dT%H:%M:%SZ")
