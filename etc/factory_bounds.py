"""Classes and functions to explore the bounds of calendar factories.

Jul 21. Module written (prior to implementation of `bound_min`,
`bound_max`) to explore the bounds of calendar factories. Provides for
evaluating the earliest start date and latest end date for which a
calendar can be instantiated without raising an error. Also records errors
raised when dates are passed beyond these limits.

Module retained in case might be useful.
"""

from __future__ import annotations
import dataclasses
import abc
import pathlib
import pickle
from typing import Literal, Type

import pandas as pd

import exchange_calendars as xcals


@dataclasses.dataclass
class FactoryBounds:
    """Bounds within which an xcals.ExchangeCalendar can be calculated.

    Parameters
    ----------
    name :
        Name of calendar with declared bounds.

    start : pd.Timestamp
        Earliest start date for which can create a calendar with end date
        as tomorrow.

    start_error :
        Error instance raised in event request a calendar with start date
        one day earlier than `start` and end date as tomorrow.

    end : pd.Timestamp
        Latest end date for which can create a calendar with start date
        as yesterday.

    end_error :
        Error instance raised in event request a calendar with end date
        one day later than `end` and start date as yesterday.
    """

    name: str
    start: pd.Timestamp
    start_error: Exception
    end: pd.Timestamp
    end_error: Exception


class _FindFactoryBounds:
    """Find start and end bounds of a given calendar factory."""

    def __init__(self, Factory: xcals.ExchangeCalendar, watch: bool = False):
        self.Factory = Factory
        self.watch = watch
        self._last_error: Exception | None

    @property
    def calendar_name(self) -> str:
        """Calendar name."""
        if isinstance(self.Factory.name, str):
            return self.Factory.name
        else:
            return self.Factory().name

    @property
    def today(self) -> pd.Timestamp:
        return pd.Timestamp.now(tz="UTC").floor("D")

    def _get_calendar(
        self,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> xcals.ExchangeCalendar:
        """Get calendar for period between now and `start` or `end`."""
        if self.watch:
            insert = f"start={start}" if start is not None else f"end={end}"
        if start is None:
            start = self.today - pd.Timedelta(1, "D")
        elif end is None:
            end = self.today + pd.Timedelta(1, "D")
        else:
            raise ValueError("`start` and `end` cannot both be None.")
        if self.watch:
            print(f"getting calendar '{self.calendar_name}' with {insert}.")
        return self.Factory(start=start, end=end)

    def _is_valid_date(
        self, date: pd.Timestamp, bound: Literal["start", "end"]
    ) -> bool:
        kwargs = {bound: date}
        try:
            self._get_calendar(**kwargs)
        except Exception as err:  # pylint: disable=broad-except
            self._last_error = err
            return False
        else:
            return True

    def _get_a_valid_date_by_trying_every_x_days(
        self,
        look_from: pd.Timestamp,
        offset: pd.DateOffset,
        bound: Literal["start", "end"],
    ) -> pd.Timestamp:
        # recursively look for a valid date every offset, return first that's valid
        if self._is_valid_date(look_from, bound):
            return look_from
        else:
            next_look_from = look_from + offset
            if (  # if start has move into the future or end into the past
                look_from <= self.today < next_look_from
                or look_from >= self.today > next_look_from
            ):
                return self.today
            else:
                return self._get_a_valid_date_by_trying_every_x_days(
                    next_look_from, offset, bound
                )

    @property
    def _first_offset(self) -> pd.DateOffset:
        return pd.DateOffset(years=100)

    def _is_first_offset(self, offset: pd.DateOffset) -> bool:
        return offset == self._first_offset or -offset == self._first_offset

    def _offset_iterator(
        self, bound: Literal["start", "end"]
    ) -> abc.Iterator[pd.DateOffset]:
        sign = 1 if bound == "start" else -1
        iterator = iter(
            [
                sign * self._first_offset,
                sign * pd.DateOffset(years=30),
                sign * pd.DateOffset(years=10),
                sign * pd.DateOffset(years=3),
                sign * pd.DateOffset(years=1),
                sign * pd.DateOffset(months=3),
                sign * pd.DateOffset(months=1),
                sign * pd.DateOffset(days=10),
                sign * pd.DateOffset(days=3),
                sign * pd.DateOffset(days=1),
            ]
        )
        return iterator

    def _is_valid_bound(
        self, date: pd.Timestamp, bound: Literal["start", "end"]
    ) -> bool:
        if not self._is_valid_date(date, bound):
            return False
        else:
            day_delta = 1 if bound == "end" else -1
            date = date + pd.Timedelta(day_delta, "D")
            return not self._is_valid_date(date, bound)

    def _try_short_cut(
        self, bound: Literal["start", "end"]
    ) -> tuple[pd.Timestamp, Exception] | None:
        """Try known likely bounds around min/max Timestamp.

        These likely bounds are caused by how special closes is calculated.

        Return None if no likely bound is a bound.
        """
        if bound == "start":
            likely_bounds = [
                pd.Timestamp("1678-01-01", tz="UTC"),
                pd.Timestamp("1679-01-01", tz="UTC"),
            ]
        else:
            likely_bounds = [
                pd.Timestamp("2260-12-31", tz="UTC"),
                pd.Timestamp("2262-04-10", tz="UTC"),
            ]

        for likely_bound in likely_bounds:
            if self._is_valid_bound(likely_bound, bound):
                assert self._last_error is not None
                return (likely_bound, self._last_error)
        return None

    @staticmethod
    def _initial_value(bound: Literal["start", "end"]) -> pd.Timestamp:
        if bound == "start":
            return pd.Timestamp.min.ceil("D").tz_localize("UTC")
        else:
            return pd.Timestamp.max.floor("D").tz_localize("UTC")

    def _get_bound(
        self, bound: Literal["start", "end"]
    ) -> tuple[pd.Timestamp, Exception]:
        self._last_error = None
        initial_value = self._initial_value(bound)

        try:
            assert not self._is_valid_bound(initial_value, bound)
        except pd.errors.OutOfBoundsDatetime as err:
            # if initial_value is a valid bound then `is_valid_bound` will
            # raise OutOfBoundsDatetime as prod beyond pandas timestamp bounds
            return (initial_value, err)

        offset_iterator = self._offset_iterator(bound)
        offset = next(offset_iterator)
        look_from = initial_value
        while offset:
            look_from += (
                offset  # avoid getting calendar with same parameters as a previous call
            )
            valid_date = self._get_a_valid_date_by_trying_every_x_days(
                look_from, offset, bound
            )
            if valid_date == look_from and self._is_first_offset(offset):
                # first attempt was valid, chances are only calculation of
                # special closes was causing error on min date. Try short-cut:
                short_cut = self._try_short_cut(bound)
                if short_cut is not None:
                    return short_cut
            look_from = valid_date - offset
            try:
                offset = next(offset_iterator)
            except StopIteration:
                break
        return (valid_date, self._last_error)

    def bounds(self) -> FactoryBounds:
        """Return valid bounds for Factory's `start` and `end` parameters.

        See find_factory_bounds.___doc___
        """
        start_bound = self._get_bound("start")
        end_bound = self._get_bound("end")
        return FactoryBounds(self.calendar_name, *start_bound, *end_bound)


def find_factory_bounds(
    Factory: xcals.ExchangeCalendar, watch: bool = False
) -> FactoryBounds:
    """Return FactoryBounds for a factory.

    Bounds deliniate the longest continuous period, which includes today,
    through which start and end dates will always return an
    xcals.ExchangeCalendar. Calling the `Factory` with a start date one day
    before the start bound, or with an end date one day after the end
    bound, will raise an error.

    Parameters
    ----------
    Factory :
        xcals.ExchangeCalendar class to query bounds of.

    watch :
        True for a live print of factory calls as the bounds are
        sought out and prodded.

    Returns
    -------
    FactoryBounds:
        Dataclass that describes bounds and associated out-of-bounds
        errors. See FactoryBounds.__doc__.

    Notes
    -----
    Uses trial and error to home in on and prod the bounds.
    """
    return _FindFactoryBounds(Factory, watch).bounds()


def _find_bounds_all_factories(watch=False) -> dict[str, FactoryBounds]:
    """Find and return Factory Bounds for all calendars.

    NOTE: This function will take a fair while to run! Pass `watch` as
    True for a live print of factory calls as the bounds are sought and
    proded.
    """
    cal_bounds = {}
    for name, Factory in xcals.calendar_utils._default_calendar_factories.items():
        cal_bounds[name] = find_factory_bounds(Factory, watch)
    return cal_bounds


def _factory_bounds_resource_path() -> pathlib.PurePath:
    path = pathlib.Path(__file__)
    path = pathlib.Path(path.parent, "resources/_factory_bounds.dat")
    assert path.exists()
    return path


def _bake_all_calendar_bounds(all_calendar_bounds: dict["str", FactoryBounds]):
    """Bake `all_calendar_bounds` to resource file.

    NOTE: CHECK passed `all_calendar_bounds` before baking.

    Parameters
    ----------
    all_calendar_bounds :
        As returned by `_find_bounds_all_factories`. CHECK return before
        baking!!
    """
    assert isinstance(all_calendar_bounds, dict)
    assert len(all_calendar_bounds) > 20
    key = list(all_calendar_bounds.keys())[0]
    assert isinstance(key, str)
    assert isinstance(all_calendar_bounds[key], FactoryBounds)
    with open(_factory_bounds_resource_path(), "wb") as file:
        pickle.dump(all_calendar_bounds, file)


def _retrieve_all_calendars_bounds() -> dict["str", FactoryBounds]:
    """Retrieve `all_calendar_bounds` from resources."""
    with open(_factory_bounds_resource_path(), "rb") as file:
        all_calendar_bounds = pickle.load(file)
    return all_calendar_bounds


_all_calendars_bounds = _retrieve_all_calendars_bounds()


def _get_all_calendars_bounds_exceptions() -> tuple[Type[Exception], ...]:
    """Exceptions the can be raised when request calendar with oob date."""
    bounds = _all_calendars_bounds
    errors = []
    for cal in bounds:
        error_types = (type(bounds[cal].start_error), type(bounds[cal].end_error))
        for error_type in error_types:
            if error_type not in errors:
                errors.append(error_type)
    return tuple(errors)


def all_calendars_bounds() -> pd.DataFrame:
    """Return DataFrame describing start and end bounds for each calendar.

    Bounds deliniate the longest continuous period, which includes today,
    through which start and end dates will always return an
    xcals.ExchangeCalendar.

    Returns
    -------
    pd.DataFrame
        Indexed with calendar names.
        Columns:
            earliest_valid_start - earliest start date from which a
                calendar can be instantiated with end date as today.
            latest_valid_end - latest end date to which a calendar can
                be instantiated with start date as today.
    """
    cal_bounds = _all_calendars_bounds
    start_bounds = []
    end_bounds = []
    for _, factory_bounds in cal_bounds.items():
        start_bounds.append(factory_bounds.start)
        end_bounds.append(factory_bounds.end)

    return pd.DataFrame(
        dict(earliest_valid_start=start_bounds, latest_valid_end=end_bounds),
        index=cal_bounds.keys(),
    )


def get_calendar_bounds(
    calendar_name: str,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Retun 2-tuple describing start and end bounds for a given calendar.

    Bounds deliniate the longest continuous period, which includes today,
    through which start and end dates will always return a calendar.
    """
    bounds = _all_calendars_bounds[calendar_name]
    return (bounds.start, bounds.end)
