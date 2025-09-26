import io
import sys

import pandas as pd

# ruff: noqa: T201

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(-1)


def _render_month(calendar, year, month, print_year):
    out = io.StringIO()

    start = f"{year}-{month}"
    end = f"{year + 1}-{1}" if month == 12 else f"{year}-{month + 1}"

    days = pd.date_range(start, end, inclusive="left")

    title = months[month - 1]
    if print_year:
        title += f" {year}"

    print(f"{title:^28}".rstrip(), file=out)
    print(" Su  Mo  Tu  We  Th  Fr  Sa", file=out)
    print(
        " " * (4 * ((days[0].weekday() + 1) % 7)),
        end="",
        file=out,
    )

    for d in days:
        if d.weekday() == 6:
            print("", file=out)  # noqa: FURB105

        if calendar.is_session(d):
            a = b = " "
        else:
            a = "["
            b = "]"

        print(
            f"{a}{d.day:>2}{b}",
            end="",
            file=out,
        )

    print("", file=out)  # noqa: FURB105
    return out.getvalue()


def _concat_lines(strings, width):
    as_lines = [string.splitlines() for string in strings]
    max_lines = max(len(lines) for lines in as_lines)
    for lines in as_lines:
        missing_lines = max_lines - len(lines)
        if missing_lines:
            lines.extend([" " * width] * missing_lines)

    rows = []
    for row_parts in zip(*as_lines, strict=False):
        row_parts = list(row_parts)  # noqa: PLW2901
        for n, row_part in enumerate(row_parts):
            missing_space = width - len(row_part)
            if missing_space:
                row_parts[n] = row_part + " " * missing_space

        rows.append("   ".join(row_parts))

    return "\n".join(row.rstrip() for row in rows)


def _int_arg(v, name):
    try:
        return int(v)
    except ValueError:
        error(f"{name} must be an integer, got: {v}")


def parse_args(argv):
    usage = f"usage: {argv[0]} CALENDAR [[[DAY] MONTH] YEAR]"

    if len(argv) == 1 or "--help" in argv or "-h" in argv:
        error(usage)

    if len(argv) > 1:
        from exchange_calendars import get_calendar  # noqa: PLC0415

        try:
            calendar = get_calendar(argv[1])
        except Exception as e:  # noqa: BLE001
            error(str(e))

    if len(argv) == 2:
        import datetime  # noqa: PLC0415

        now = datetime.datetime.now()
        year = now.year
        month = now.month
    elif len(argv) == 3:
        year = _int_arg(argv[2], "YEAR")
        month = None
    elif len(argv) == 4:
        month = _int_arg(argv[2], "MONTH")
        year = _int_arg(argv[3], "YEAR")
    else:
        error(usage)

    return calendar, year, month


def main(argv=None):
    """Print a unix-cal like calendar but indicate which days are trading
    sessions.
    """
    if argv is None:
        argv = sys.argv
    calendar, year, month = parse_args(argv)

    if month is not None:
        print(_render_month(calendar, year, month, print_year=True))
    else:
        month_strings = [
            [
                _render_month(
                    calendar,
                    year,
                    row * 3 + column + 1,
                    print_year=False,
                )
                for column in range(3)
            ]
            for row in range(4)
        ]
        print(f"{year:^88}\n".rstrip())
        print("\n\n".join(_concat_lines(cs, 28) for cs in month_strings))


if __name__ == "__main__":
    main()
