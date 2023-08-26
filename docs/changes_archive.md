**NOTE**: This file is NOT a comprehensive changes log but rather an archive of sections temporarily included to the README to advise of significant changes.

## **v4 released** (June 2022)

**The earliest stable version of v4 is 4.0.1** (not 4.0).

### What's changed?

Version 4.0.1 completes the transition to a more consistent interface across the package. The most significant changes are:

* **Sessions are now timezone-naive** (previously UTC).
* Schedule columns now have timezone set as UTC (whilst the times have always been defined in terms of UTC, previously the dtype was timezone-naive).
* The following schedule columns were renamed:
    * 'market_open' renamed as 'open'.
    * 'market_close' renamed as 'close'.
* Default calendar 'side' for all calendars is now "left" (previously "right" for 24-hour calendars and "both" for all others). This **changes the minutes that are considered trading minutes by default** (see [minutes tutorial](docs/tutorials/minutes.ipynb) for an explanation of trading minutes).
* The 'count' parameter of `sessions_window` and `minutes_window` methods now reflects the window length (previously window length + 1).
* New `is_open_at_time` calendar method to evaluate if an exchange is open as at a specific instance (as opposed to over an evaluated minute).
* The minimum Python version supported is now 3.8 (previously 3.7).
* Parameters have been renamed for some methods (list [here](#Methods-with-a-parameter-renamed-in-40))
* The following methods have been deprecated:
    * `sessions_opens` (use `.opens[start:end]`)
    * `sessions_closes` (use `.closes[start:end]`)
* Methods deprecated in 3.4 have been removed (lists [here](#Methods-renamed-in-version-34-and-removed-in-40) and [here](#Other-methods-deprecated-in-34-and-removed-in-40))

See the [4.0 release todo](https://github.com/gerrymanoim/exchange_calendars/issues/61) for a full list of changes and corresponding PRs.

Please offer any feedback at the [v4 discussion](https://github.com/gerrymanoim/exchange_calendars/discussions/202).

## **Changes in 3.4** (released October 2021)
The 3.4 release introduced notable new features and documentation, including:

* [Tutorials](#Tutorials). Five of them!
* New calendar methods [#71](https://github.com/gerrymanoim/exchange_calendars/pull/71) (see [calendar_methods.ipynb](docs/tutorials/calendar_methods.ipynb) for usage), including:
  * trading_index (tutorial [trading_index.ipynb](docs/tutorials/trading_index.ipynb))
  * is_trading_minute
  * is_break_minute
  * minute_offset
  * session_offset
  * minute_offset_by_sessions
* Calendar's now have a `side` parameter to determine which of the open, close, break-start and break-end minutes are treated as trading minutes [#71](https://github.com/gerrymanoim/exchange_calendars/pull/71).
* 24 hour calendars are now truly 24 hours (open/close times are no longer one minute later/earlier than the actual open/close) [#71](https://github.com/gerrymanoim/exchange_calendars/pull/71).
* Some calendar methods have been renamed to improve consistency (table of changes [here](#Methods-renamed-in-version-34)) [#85](https://github.com/gerrymanoim/exchange_calendars/issues/85). The previous names will continue to be available until version 4.0. NOTE: Some newly named methods have also made changes to parameter names, for example from `session_label` to `session` and from `start_session_label` to `start`.
* Under-the-bonnet work has sped up many methods.
* A test suite overhaul ([#71](https://github.com/gerrymanoim/exchange_calendars/pull/71), [#92](https://github.com/gerrymanoim/exchange_calendars/pull/92), [#96](https://github.com/gerrymanoim/exchange_calendars/pull/96)) has made it simpler to define and test calendars.

Please offer any feedback at the [3.4 discussion](https://github.com/gerrymanoim/exchange_calendars/discussions/107).
