"""
This script can be used to generate the CSV files used in the exchange calendar
tests. The CSVs include a calendar's sessions, open times, close times,
break_start times and break_end times.

This script can be run from the root of the repository with:
    $ python etc/make_exchange_calendar_test_csv.py <calendar_iso_code> <start> <end>
where:
    <calendar_iso_code>
        Code for the corresponding calendar, e.g. "XNYS"

    <start> optional, default: "existing" if existing, else "default"
        First session to include to CSV file. Can take any of:
            A date, for example "1998-06-15".
            "existing" to use first session of any exising csv file.
            "default" to use calendar's default start date.

    <end> optional, default: "default"
        NB if <end> is provided then <start> MUST also be provided.
        Last session to include to CSV file. Can take any of:
            A date, for example "2026-06-15".
            "existing" to use last session of any exising csv file.
            "default" to use calendar's default end date.
"""

import sys
import pathlib

import pandas as pd

from exchange_calendars import get_calendar

cal_name = sys.argv[1].upper()

filename = cal_name.replace("/", "-").lower() + ".csv"
path = pathlib.Path(__file__).parents[1].joinpath("tests/resources", filename)

if len(sys.argv) > 2:
    start_arg = sys.argv[2]
else:
    start_arg = "existing" if path.is_file else "default"
end_arg = sys.argv[3] if len(sys.argv) > 3 else "default"

if start_arg == "existing" or end_arg == "existing":
    assert path.is_file
    df = pd.read_csv(
        path,
        index_col=0,
        parse_dates=[0, 1, 2, 3, 4],
        infer_datetime_format=True,
    )

if start_arg == "existing":
    start = df.index[0].tz_localize(None)
elif start_arg == "default":
    start = None
else:
    start = start_arg

if end_arg == "existing":
    end = df.index[-1].tz_localize(None)
elif end_arg == "default":
    end = None
else:
    end = end_arg

cal = get_calendar(cal_name, start=start, end=end)

df = pd.DataFrame(
    list(zip(cal.opens, cal.closes, cal.break_starts, cal.break_ends)),
    columns=["open", "close", "break_start", "break_end"],
    index=cal.closes.index,
)

print(f"Writing test CSV file to {path}")
df.to_csv(path, date_format="%Y-%m-%dT%H:%M:%SZ")
