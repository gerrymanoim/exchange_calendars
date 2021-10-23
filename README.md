# exchange_calendars

[![PyPI](https://img.shields.io/pypi/v/exchange-calendars)](https://pypi.org/project/exchange-calendars/) ![Python Support](https://img.shields.io/pypi/pyversions/exchange_calendars) ![PyPI Downloads](https://img.shields.io/pypi/dd/exchange-calendars) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python library for defining and querying calendars for security exchanges.

Calendars for more than [50 exchanges](#Calendars) available out-the-box! If you still can't find the calendar you're looking for, [create a new one](#How-can-I-create-a-new-calendar)!

## **What's new in 3.4?** (October 2021)
Quite a bit!

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
* As ever, specific calendars have been updated and improved. Thank you to those who have contributed since the last release:
  * XKRX improvements by [@elbakramer](https://github.com/elbakramer) [#78](https://github.com/gerrymanoim/exchange_calendars/pull/78).
  * XBOM corrections by [@rajeshyogeshwar](https://github.com/rajeshyogeshwar) [#97](https://github.com/gerrymanoim/exchange_calendars/pull/97).

## Installation

```bash
$ pip install exchange_calendars
```

## Quick Start

```python
import exchange_calendars as xcals
```

Get a list of available calendars:

```python
>>> xcals.get_calendar_names(include_aliases=False)[5:10]
['CMES', 'IEPA', 'XAMS', 'XASX', 'XBKK']
```

Get a calendar:

```python
>>> xnys = xcals.get_calendar("XNYS")  # New York Stock Exchange
>>> xhkg = xcals.get_calendar(
        "XHKG",
        start="2018-01",
        end="2021-12-31",
        side="left"
)  # Hong Kong Stock Exchange
```
Query the schedule:

```python
>>> xhkg.schedule.loc["2020-12-29":"2021-01-05"]
```
<!-- output from `xhkg.schedule.loc["2020-12-29":"2021-01-05"].to_html()` -->
<table border="1" class="dataframe">  <thead>    <tr style="text-align: right; font-size: 13px">      <th></th>      <th>market_open</th>      <th>break_start</th>      <th>break_end</th>      <th>market_close</th>    </tr>  </thead>  <tbody style="text-align: right; font-size: 11px">    <tr>      <th>2020-12-29 00:00:00+00:00</th>      <td>2020-12-29 01:30:00</td>      <td>2020-12-29 04:00:00</td>      <td>2020-12-29 05:00:00</td>      <td>2020-12-29 08:00:00</td>    </tr>    <tr>      <th>2020-12-30 00:00:00+00:00</th>      <td>2020-12-30 01:30:00</td>      <td>2020-12-30 04:00:00</td>      <td>2020-12-30 05:00:00</td>      <td>2020-12-30 08:00:00</td>    </tr>    <tr>      <th>2020-12-31 00:00:00+00:00</th>      <td>2020-12-31 01:30:00</td>      <td>NaT</td>      <td>NaT</td>      <td>2020-12-31 04:00:00</td>    </tr>    <tr>      <th>2021-01-04 00:00:00+00:00</th>      <td>2021-01-04 01:30:00</td>      <td>2021-01-04 04:00:00</td>      <td>2021-01-04 05:00:00</td>      <td>2021-01-04 08:00:00</td>    </tr>    <tr>      <th>2021-01-05 00:00:00+00:00</th>      <td>2021-01-05 01:30:00</td>      <td>2021-01-05 04:00:00</td>      <td>2021-01-05 05:00:00</td>      <td>2021-01-05 08:00:00</td>    </tr>  </tbody></table>

### Working with **sessions**
```python
>>> xnys.is_session("2020-01-01")
False

>>> xnys.sessions_in_range("2021-01-01", "2021-01-11")
DatetimeIndex(['2021-01-04 00:00:00+00:00', '2021-01-05 00:00:00+00:00',
               '2021-01-06 00:00:00+00:00', '2021-01-07 00:00:00+00:00',
               '2021-01-08 00:00:00+00:00', '2021-01-11 00:00:00+00:00'],
              dtype='datetime64[ns, UTC]', freq='C')

>>> xnys.sessions_window("2021-01-04", 7)
DatetimeIndex(['2021-01-04 00:00:00+00:00', '2021-01-05 00:00:00+00:00',
               '2021-01-06 00:00:00+00:00', '2021-01-07 00:00:00+00:00',
               '2021-01-08 00:00:00+00:00', '2021-01-11 00:00:00+00:00',
               '2021-01-12 00:00:00+00:00', '2021-01-13 00:00:00+00:00'],
              dtype='datetime64[ns, UTC]', freq='C')

>>> xnys.date_to_session_("2021-01-01", direction="next")
Timestamp('2021-01-04 00:00:00+0000', tz='UTC', freq='C')

>>> xnys.previous_session("2021-01-11")
Timestamp('2021-01-08 00:00:00+0000', tz='UTC', freq='C')

>>> xhkg.trading_index(
...     "2020-12-30",
...     "2020-12-31",
...     period="90T",
...     force_close=True,
...     force_break_close=True
... )
IntervalIndex([[2020-12-30 01:30:00, 2020-12-30 03:00:00), [2020-12-30 03:00:00, 2020-12-30 04:00:00), [2020-12-30 05:00:00, 2020-12-30 06:30:00), [2020-12-30 06:30:00, 2020-12-30 08:00:00), [2020-12-31 01:30:00, 2020-12-31 03:00:00), [2020-12-31 03:00:00, 2020-12-31 04:00:00)],
              closed='left',
              dtype='interval[datetime64[ns, UTC]]')
```
See the [sessions tutorial](docs/tutorials/sessions.ipynb) for a deeper dive into sessions.

### Working with **minutes**  
```python
>>> xhkg.session_minutes("2021-01-04")
DatetimeIndex(['2021-01-04 01:30:00+00:00', '2021-01-04 01:31:00+00:00',
               '2021-01-04 01:32:00+00:00', '2021-01-04 01:33:00+00:00',
               '2021-01-04 01:34:00+00:00', '2021-01-04 01:35:00+00:00',
               '2021-01-04 01:36:00+00:00', '2021-01-04 01:37:00+00:00',
               '2021-01-04 01:38:00+00:00', '2021-01-04 01:39:00+00:00',
               ...
               '2021-01-04 07:50:00+00:00', '2021-01-04 07:51:00+00:00',
               '2021-01-04 07:52:00+00:00', '2021-01-04 07:53:00+00:00',
               '2021-01-04 07:54:00+00:00', '2021-01-04 07:55:00+00:00',
               '2021-01-04 07:56:00+00:00', '2021-01-04 07:57:00+00:00',
               '2021-01-04 07:58:00+00:00', '2021-01-04 07:59:00+00:00'],
              dtype='datetime64[ns, UTC]', length=330, freq=None)

>>> mins = [ "2021-01-04 " + tm for tm in ["01:29", "01:30", "04:20", "07:59", "08:00"] ]
>>> [ xhkg.is_trading_minute(minute) for minute in mins ]
[False, True, False, True, False]

>>> xhkg.is_break_minute("2021-01-04 04:20")
True

>>> xhkg.previous_close("2021-01-04 21:10")
Timestamp('2021-01-04 08:00:00+0000', tz='UTC')

>>> xhkg.previous_minute("2021-01-04 21:10")
Timestamp('2021-01-04 07:59:00+0000', tz='UTC')
```
Check out the [minutes tutorial](docs/tutorials/minutes.ipynb) for a deeper dive that includes an explanation of the concept of 'minutes' and how the "side" option determines which minutes are treated as trading minutes.

## Tutorials
[sessions.ipynb](docs/tutorials/sessions.ipynb) - all things [sessions](#Working-with-sessions).  
[minutes.ipynb](docs/tutorials/minutes.ipynb) - all things [minutes](#Working-with-minutes). Don't miss this one!  
[calendar_properties.ipynb](docs/tutorials/calendar_properties.ipynb) - a walk through the schedule and all other calendar properties.  
[calendar_methods.ipynb](docs/tutorials/calendar_methods.ipynb) - a walk through all the methods available to interrogate a calendar.  
[trading_index.ipynb](docs/tutorials/trading_index.ipynb) - a method that warrants a tutorial all of its own.

Hopefully you'll find that `exchange_calendars` has the method you need to get the information you want. If it doesn't, either [PR](https://github.com/gerrymanoim/exchange_calendars/pulls) it or [raise an issue](https://github.com/gerrymanoim/exchange_calendars/issues) and let us know!

## Command Line Usage
Print a unix-cal like calendar straight from the command line (holidays are indicated by brackets)...

```bash
ecal XNYS 2020
```
                                            2020
            January                        February                        March
    Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa
                [ 1]  2   3 [ 4]                           [ 1]
    [ 5]  6   7   8   9  10 [11]   [ 2]  3   4   5   6   7 [ 8]   [ 1]  2   3   4   5   6 [ 7]
    [12] 13  14  15  16  17 [18]   [ 9] 10  11  12  13  14 [15]   [ 8]  9  10  11  12  13 [14]
    [19][20] 21  22  23  24 [25]   [16][17] 18  19  20  21 [22]   [15] 16  17  18  19  20 [21]
    [26] 27  28  29  30  31        [23] 24  25  26  27  28 [29]   [22] 23  24  25  26  27 [28]
                                                                  [29] 30  31

            April                           May                            June
    Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa
                  1   2   3 [ 4]                         1 [ 2]         1   2   3   4   5 [ 6]
    [ 5]  6   7   8   9 [10][11]   [ 3]  4   5   6   7   8 [ 9]   [ 7]  8   9  10  11  12 [13]
    [12] 13  14  15  16  17 [18]   [10] 11  12  13  14  15 [16]   [14] 15  16  17  18  19 [20]
    [19] 20  21  22  23  24 [25]   [17] 18  19  20  21  22 [23]   [21] 22  23  24  25  26 [27]
    [26] 27  28  29  30            [24][25] 26  27  28  29 [30]   [28] 29  30
                                   [31]

                July                          August                       September
    Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa
                  1   2 [ 3][ 4]                           [ 1]             1   2   3   4 [ 5]
    [ 5]  6   7   8   9  10 [11]   [ 2]  3   4   5   6   7 [ 8]   [ 6][ 7]  8   9  10  11 [12]
    [12] 13  14  15  16  17 [18]   [ 9] 10  11  12  13  14 [15]   [13] 14  15  16  17  18 [19]
    [19] 20  21  22  23  24 [25]   [16] 17  18  19  20  21 [22]   [20] 21  22  23  24  25 [26]
    [26] 27  28  29  30  31        [23] 24  25  26  27  28 [29]   [27] 28  29  30
                                   [30] 31

            October                        November                       December
    Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa     Su  Mo  Tu  We  Th  Fr  Sa
                      1   2 [ 3]                                            1   2   3   4 [ 5]
    [ 4]  5   6   7   8   9 [10]   [ 1]  2   3   4   5   6 [ 7]   [ 6]  7   8   9  10  11 [12]
    [11] 12  13  14  15  16 [17]   [ 8]  9  10  11  12  13 [14]   [13] 14  15  16  17  18 [19]
    [18] 19  20  21  22  23 [24]   [15] 16  17  18  19  20 [21]   [20] 21  22  23  24 [25][26]
    [25] 26  27  28  29  30 [31]   [22] 23  24  25 [26] 27 [28]   [27] 28  29  30  31
                                   [29] 30

```bash
ecal XNYS 1 2020
```

            January 2020
    Su  Mo  Tu  We  Th  Fr  Sa
                [ 1]  2   3 [ 4]
    [ 5]  6   7   8   9  10 [11]
    [12] 13  14  15  16  17 [18]
    [19][20] 21  22  23  24 [25]
    [26] 27  28  29  30  31

## Methods renamed in version 3.4
| Previous Name | New Name |
| ------------- | -------- |
| previous_session_label | previous_session |
| next_session_label | next_session |
| date_to_session_label | date_to_session |
| minute_to_session_label | minute_to_session |
| open_and_close_for_session | session_open_close |
| break_start_and_end_for_session | session_break_start_end |
| minutes_for_session | session_minutes |
| minute_index_to_session_labels | minutes_to_sessions |
| all_sessions | sessions |
| all_minutes | minutes |
| all_minutes_nanos | minutes_nanos |
| first_trading_minute | first_minute |
| last_trading_minute | last_minute |
| first_trading_session | first_session |
| last_trading_session | last_session |
| has_breaks | sessions_has_break |
| market_opens_nanos | opens_nanos |
| market_closes_nanos | closes_nanos |
| market_break_starts_nanos | break_starts_nanos |
| market_break_ends_nanos | break_ends_nanos |

## What to expect in 4.0? (January 2022)
Major anticipated changes in 4.0 include the following (see the [path to 4.0](https://github.com/gerrymanoim/exchange_calendars/issues/61) for a fuller list):
* Changes to the timezone of returned sessions and times (these changes are not yet set in stone - please have your say [here](https://github.com/gerrymanoim/exchange_calendars/issues/42)).
  * Schedule times to change from tz-naive to "UTC".
  * Sessions to change from "UTC" to tz-naive.
* Renaming of some methods and method parameters to provide consistency across the package.
* Minimum supported Python version to advance from 3.7 to 3.8.
* For those [methods renamed in 3.4](#Methods-renamed-in-version-34), the previous method names will be removed.

## Frequently Asked Questions

### **How can I create a new calendar?**

First off, make sure the calendar you're after hasn't already been defined; exchange calendars comes with over [50 pre-defined calendars](#Calendars), including major security exchanges.

If you can't find what you're after, a custom calendar can be created as a subclass of [ExchangeCalendar](exchange_calendars/exchange_calendar.py). [This workflow](.github/pull_request_template.md) describes the process to add a new calendar to `exchange_calendars`. Just follow the relevant parts.

To access the new calendar via `get_calendar` call either `xcals.register_calendar` or `xcals.register_calendar_type` to register, respectively, a specific calendar instance or a calendar factory (i.e. the subclass).

### **Can I contribute a new calendar to exchange calendars?**

Yes please! The workflow can be found [here](.github/pull_request_template.md).

### **`<calendar>` is missing a holiday, has a wrong time, should have a break etc...**

**All** of the exchange calendars are maintained by user contributions. If a calendar you care about needs revising, please open a [PR](https://github.com/gerrymanoim/exchange_calendars/pulls) - that's how this thing works!

You'll find the workflow to modify an existing calendar [here](.github/pull_request_template.md).

### **What times are considered open and closed?**

`exchange_calendars` attempts to be broadly useful by considering an exchange to be open only during periods of regular trading. During any pre-trading, post-trading or auction period the exchange is treated as closed. An exchange is also treated as closed during any observed lunch break.

See the [minutes tutorial](docs/tutorials/minutes.ipynb) for a detailed explanation of which minutes an exchange is considered open over. If you previously used `trading_calendars`, or `exchange_calendars` prior to release 3.4, then this is the place to look for answers to questions of how the definition of trading minutes has changed over time (and is now stable and flexible!).

## Calendars

| Exchange                        | ISO Code | Country        | Version Added | Exchange Website (English)                                   |
| ------------------------------- | -------- | -------------- | ------------- | ------------------------------------------------------------ |
| New York Stock Exchange         | XNYS     | USA            | 1.0           | https://www.nyse.com/index                                   |
| CBOE Futures                    | XCBF     | USA            | 1.0           | https://markets.cboe.com/us/futures/overview/                |
| Chicago Mercantile Exchange     | CMES     | USA            | 1.0           | https://www.cmegroup.com/                                    |
| ICE US                          | IEPA     | USA            | 1.0           | https://www.theice.com/index                                 |
| Toronto Stock Exchange          | XTSE     | Canada         | 1.0           | https://www.tsx.com/                                         |
| BMF Bovespa                     | BVMF     | Brazil         | 1.0           | http://www.b3.com.br/en_us/                                  |
| London Stock Exchange           | XLON     | England        | 1.0           | https://www.londonstockexchange.com/                         |
| Euronext Amsterdam              | XAMS     | Netherlands    | 1.2           | https://www.euronext.com/en/regulation/amsterdam             |
| Euronext Brussels               | XBRU     | Belgium        | 1.2           | https://www.euronext.com/en/regulation/brussels              |
| Euronext Lisbon                 | XLIS     | Portugal       | 1.2           | https://www.euronext.com/en/regulation/lisbon                |
| Euronext Paris                  | XPAR     | France         | 1.2           | https://www.euronext.com/en/regulation/paris                 |
| Frankfurt Stock Exchange        | XFRA     | Germany        | 1.2           | http://en.boerse-frankfurt.de/                               |
| SIX Swiss Exchange              | XSWX     | Switzerland    | 1.2           | https://www.six-group.com/en/home.html                       |
| Tokyo Stock Exchange            | XTKS     | Japan          | 1.2           | https://www.jpx.co.jp/english/                               |
| Austrialian Securities Exchange | XASX     | Australia      | 1.3           | https://www.asx.com.au/                                      |
| Bolsa de Madrid                 | XMAD     | Spain          | 1.3           | https://www.bolsamadrid.es                                   |
| Borsa Italiana                  | XMIL     | Italy          | 1.3           | https://www.borsaitaliana.it                                 |
| New Zealand Exchange            | XNZE     | New Zealand    | 1.3           | https://www.nzx.com/                                         |
| Wiener Borse                    | XWBO     | Austria        | 1.3           | https://www.wienerborse.at/en/                               |
| Hong Kong Stock Exchange        | XHKG     | Hong Kong      | 1.3           | https://www.hkex.com.hk/?sc_lang=en                          |
| Copenhagen Stock Exchange       | XCSE     | Denmark        | 1.4           | http://www.nasdaqomxnordic.com/                              |
| Helsinki Stock Exchange         | XHEL     | Finland        | 1.4           | http://www.nasdaqomxnordic.com/                              |
| Stockholm Stock Exchange        | XSTO     | Sweden         | 1.4           | http://www.nasdaqomxnordic.com/                              |
| Oslo Stock Exchange             | XOSL     | Norway         | 1.4           | https://www.oslobors.no/ob_eng/                              |
| Irish Stock Exchange            | XDUB     | Ireland        | 1.4           | http://www.ise.ie/                                           |
| Bombay Stock Exchange           | XBOM     | India          | 1.5           | https://www.bseindia.com                                     |
| Singapore Exchange              | XSES     | Singapore      | 1.5           | https://www.sgx.com                                          |
| Shanghai Stock Exchange         | XSHG     | China          | 1.5           | http://english.sse.com.cn                                    |
| Korea Exchange                  | XKRX     | South Korea    | 1.6           | http://global.krx.co.kr                                      |
| Iceland Stock Exchange          | XICE     | Iceland        | 1.7           | http://www.nasdaqomxnordic.com/                              |
| Poland Stock Exchange           | XWAR     | Poland         | 1.9           | http://www.gpw.pl                                            |
| Santiago Stock Exchange         | XSGO     | Chile          | 1.9           | https://www.bolsadesantiago.com/                             |
| Colombia Securities Exchange    | XBOG     | Colombia       | 1.9           | https://www.bvc.com.co/nueva/https://www.bvc.com.co/nueva/   |
| Mexican Stock Exchange          | XMEX     | Mexico         | 1.9           | https://www.bmv.com.mx                                       |
| Lima Stock Exchange             | XLIM     | Peru           | 1.9           | https://www.bvl.com.pe                                       |
| Prague Stock Exchange           | XPRA     | Czech Republic | 1.9           | https://www.pse.cz/en/                                       |
| Budapest Stock Exchange         | XBUD     | Hungary        | 1.10          | https://bse.hu/                                              |
| Athens Stock Exchange           | ASEX     | Greece         | 1.10          | http://www.helex.gr/                                         |
| Istanbul Stock Exchange         | XIST     | Turkey         | 1.10          | https://www.borsaistanbul.com/en/                            |
| Johannesburg Stock Exchange     | XJSE     | South Africa   | 1.10          | https://www.jse.co.za/z                                      |
| Malaysia Stock Exchange         | XKLS     | Malaysia       | 1.11          | http://www.bursamalaysia.com/market/                         |
| Moscow Exchange                 | XMOS     | Russia         | 1.11          | https://www.moex.com/en/                                     |
| Philippine Stock Exchange       | XPHS     | Philippines    | 1.11          | https://www.pse.com.ph/                                      |
| Stock Exchange of Thailand      | XBKK     | Thailand       | 1.11          | https://www.set.or.th/set/mainpage.do?language=en&country=US |
| Indonesia Stock Exchange        | XIDX     | Indonesia      | 1.11          | https://www.idx.co.id/                                       |
| Taiwan Stock Exchange Corp.     | XTAI     | Taiwan         | 1.11          | https://www.twse.com.tw/en/                                  |
| Buenos Aires Stock Exchange     | XBUE     | Argentina      | 1.11          | https://www.bcba.sba.com.ar/                                 |
| Pakistan Stock Exchange         | XKAR     | Pakistan       | 1.11          | https://www.psx.com.pk/                                      |
| Xetra                           | XETR     | Germany        | 2.1           | https://www.xetra.com/                                       |
| Tel Aviv Stock Exchange         | XTAE     | Israel         | 2.1           | https://www.tase.co.il/                                      |
| Astana International Exchange   | AIXK     | Kazakhstan     | 3.2           | https://www.aix.kz/                                          |
| Bucharest Stock Exchange        | XBSE     | Romania        | 3.2           | https://www.bvb.ro/                                          |

> Note that exchange calendars are defined by their [ISO-10383](https://www.iso20022.org/10383/iso-10383-market-identifier-codes) market identifier code.
