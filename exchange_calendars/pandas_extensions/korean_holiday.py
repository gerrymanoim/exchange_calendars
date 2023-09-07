import datetime
import pandas as pd
from zoneinfo import ZoneInfo

from pandas.tseries.offsets import Day
from korean_lunar_calendar import KoreanLunarCalendar

from .holiday import Holiday
from .offsets import _is_normalized


def is_naive(dt):
    return dt.tzinfo is None


class KoreanHoliday(Holiday):
    _timezone = ZoneInfo("Asia/Seoul")
    _local_timezone = datetime.datetime.now().astimezone().tzinfo

    _computed_holidays = pd.Series([], index=pd.DatetimeIndex([]), dtype=object)
    _alternate_holidays_cache = pd.Series(
        pd.DatetimeIndex([]),
        index=pd.DatetimeIndex([]),
    )

    def _apply_rule(
        self, dates, apply_offset=True, apply_observance=True, register_holidays=True
    ):
        dates = super()._apply_rule(dates, apply_offset, apply_observance)
        if register_holidays:
            for date in dates:
                assert is_naive(date)
                assert _is_normalized(date)
                if date not in KoreanHoliday._computed_holidays.index:
                    KoreanHoliday._computed_holidays[date] = self
        return dates


def to_korean_datetime(dt):
    dt = pd.to_datetime(dt)
    if dt.tz is None:
        dt = dt.tz_localize(KoreanHoliday._local_timezone)
    dt = dt.tz_convert(KoreanHoliday._timezone)
    return dt


def is_saturday(dt):
    return dt.weekday() == 5


def is_sunday(dt):
    return dt.weekday() == 6


def is_holiday_saturday(dt):
    is_holiday_since = pd.Timestamp("1998-12-07")
    return dt >= is_holiday_since.tz_localize(dt.tzinfo) and is_saturday(dt)


def is_already_korean_holiday(dt):
    dt = pd.Timestamp(dt).tz_localize(None).normalize()
    return dt in KoreanHoliday._computed_holidays


original_alternative_holiday_since = pd.Timestamp(
    "2014-01-01"
)  # alternative holidays have been applied since year 2014
revised_alternative_holiday_since = pd.Timestamp(
    "2021-08-04"
)  # and expanded since 2021-08-04


def alternative_holiday_func(dt, is_already_holiday, since):
    if dt >= since:
        dt = pd.Timestamp(dt)
        dt_tzinfo = dt.tzinfo
        key_dt = dt.tz_localize(None).normalize()
        time_offset = dt.tz_localize(None) - key_dt
        if key_dt not in KoreanHoliday._alternate_holidays_cache.index:
            while is_already_holiday(dt):
                dt += Day(1)
            value_dt = dt.tz_localize(None).normalize()
            KoreanHoliday._alternate_holidays_cache[key_dt] = value_dt
        dt = KoreanHoliday._alternate_holidays_cache[key_dt]
        dt = dt + time_offset
        dt = dt.tz_localize(dt_tzinfo)
    return dt


def is_already_holiday(dt):
    return is_holiday_saturday(dt) or is_sunday(dt) or is_already_korean_holiday(dt)


def is_already_holiday_for_alternative_holiday_including_saturday(dt):
    # originally since 2014
    #  1. Children's Day
    # added since 2021-08-04
    #  2. Independence Movement Day
    #  3. National Liberation Day
    #  4. Korean National Foundation Day
    #  5. Hangul Proclamation Day
    return is_saturday(dt) or is_sunday(dt) or is_already_korean_holiday(dt)


def is_already_holiday_for_alternative_holiday_without_saturday(dt):
    # originally since 2014
    #  1. Seollal
    #  2. Chuseok
    return is_sunday(dt) or is_already_korean_holiday(dt)


def alternative_holiday_for_seollal_and_chuseok(dt):
    return alternative_holiday_func(
        dt,
        is_already_holiday_for_alternative_holiday_without_saturday,
        original_alternative_holiday_since,
    )


def alternative_holiday_for_childrens_day(dt):
    return alternative_holiday_func(
        dt,
        is_already_holiday_for_alternative_holiday_including_saturday,
        original_alternative_holiday_since,
    )


def alternative_holiday(dt):
    return alternative_holiday_func(
        dt,
        is_already_holiday_for_alternative_holiday_including_saturday,
        revised_alternative_holiday_since,
    )


def next_business_day(dt):
    while is_already_holiday(dt):
        dt += Day(1)
    return dt


def last_business_day(dt):
    while is_already_holiday(dt):
        dt -= Day(1)
    return dt


class KoreanSolarHoliday(KoreanHoliday):
    pass


def korean_lunar_to_solar(year, month, day, is_intercalation=False):
    calendar = KoreanLunarCalendar()
    is_valid = calendar.setLunarDate(year, month, day, is_intercalation)
    if not is_valid:
        raise ValueError(
            "Invalid date for lunar date: (year=%r, month=%r, day=%r, is_intercalation=%r)"
            % (year, month, day, is_intercalation)
        )
    return (calendar.solarYear, calendar.solarMonth, calendar.solarDay)


def korean_lunar_to_solar_datetime(dt, is_intercalation=False):
    year, month, day = korean_lunar_to_solar(
        dt.year, dt.month, dt.day, is_intercalation=is_intercalation
    )
    return dt.replace(year, month, day)


def korean_solar_to_lunar(year, month, day):
    calendar = KoreanLunarCalendar()
    is_valid = calendar.setSolarDate(year, month, day)
    if not is_valid:
        raise ValueError(
            "Invalid date for solar date: (year=%r, month=%r, day=%r)"
            % (year, month, day)
        )
    return (calendar.lunarYear, calendar.lunarMonth, calendar.lunarDay)


def korean_solar_to_lunar_datetime(dt, round_down: bool):
    """This method sets the year, month and day fields on a pd.Timestamp to the equivalent lunar ones.

    The problem is that not all lunar calendar dates can be stored in a Gregorian date.
    For example, 2022-03-31 (Gregorian) corresponds to 2022-02-29 (Korean lunar). The latter
    is not a valid Gregorian date. So, we introduce a rounding flag. If round_down is True,
    then this method will decrement the solar date until the lunar date happens to be a valid
    Gregorian one. If round_down is False, then the solar date will be incremented analogously.
    """
    while True:
        year, month, day = korean_solar_to_lunar(dt.year, dt.month, dt.day)
        try:
            datetime.date(year, month, day)
            return dt.replace(year, month, day)
        except ValueError:
            dt += datetime.timedelta(days=-1 if round_down else 1)


class KoreanLunarHoliday(KoreanHoliday):
    _max_solar_end_date = pd.to_datetime(
        str(KoreanLunarCalendar.KOREAN_SOLAR_MAX_VALUE), format="%Y%m%d"
    )
    _max_lunar_end_date = pd.to_datetime(
        str(KoreanLunarCalendar.KOREAN_LUNAR_MAX_VALUE), format="%Y%m%d"
    )

    def _reference_dates(self, start_date, end_date, strict=False):
        solar_start_date = start_date
        solar_end_date = end_date

        # Restrict date range to fall into supported range of korean_lunar_calendar library
        if solar_end_date > self._max_solar_end_date:
            if not strict and solar_start_date < self._max_solar_end_date:
                solar_end_date = self._max_solar_end_date
            else:
                raise ValueError(
                    "Cannot support date range after %r, but %r ~ %r given"
                    % (self._max_solar_end_date, start_date, end_date)
                )

        # Get lunar reference dates
        lunar_start_date = korean_solar_to_lunar_datetime(
            solar_start_date, round_down=True
        )
        lunar_end_date = korean_solar_to_lunar_datetime(
            solar_end_date, round_down=False
        )
        dates = super()._reference_dates(lunar_start_date, lunar_end_date)

        # Still restrict date range to fall into supported range of korean_lunar_calendar library
        dates = dates[dates <= self._max_lunar_end_date]

        # Convert lunar dates to solar dates
        dates = dates.to_series()
        dates = dates.map(korean_lunar_to_solar_datetime)
        dates = pd.DatetimeIndex(dates)

        return dates[(dates >= start_date) & (dates < end_date)]
