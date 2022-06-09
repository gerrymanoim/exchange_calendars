**NOTE**: This file is NOT a comprehensive changes log but rather an archive of sections temporarily included to the README to advise of significant changes.

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
