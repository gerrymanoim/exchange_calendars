from pathlib import Path
import requests

import pandas as pd

# Precomputed/adhoc KRX holidays can be checked here
# http://open.krx.co.kr/contents/MKD/01/0110/01100305/MKD01100305.jsp
# http://global.krx.co.kr/contents/GLB/05/0501/0501110000/GLB0501110000.jsp

download_holidays_as_dict_oldest_year_available = 1975


def download_krx_holidays_as_dict(year=None, page_first_call=False):
    now = pd.Timestamp.now("Asia/Seoul")

    if year is None:
        year = now.year

    if year < download_holidays_as_dict_oldest_year_available:
        raise ValueError(
            "Year cannot be older than"
            f" {download_holidays_as_dict_oldest_year_available} but {year} given"
        )

    def generate_otp():
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Host": "global.krx.co.kr",
            "Referer": "http://global.krx.co.kr/contents/GLB/05/0501/0501110000/GLB0501110000.jsp",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",  # noqa: E501
            "X-Requested-With": "XMLHttpRequest",
        }
        params = {
            "bld": "GLB/05/0501/0501110000/glb0501110000_01",
            "name": "form",
            "_": str(int(now.timestamp() * 1000)),
        }
        response = requests.get(
            "http://global.krx.co.kr/contents/COM/GenerateOTP.jspx",
            headers=headers,
            params=params,
        )
        return response.content

    code = generate_otp()
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Host": "global.krx.co.kr",
        "Origin": "http://global.krx.co.kr",
        "Referer": "http://global.krx.co.kr/contents/GLB/05/0501/0501110000/GLB0501110000.jsp",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",  # noqa: E501
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {
        "search_bas_yy": str(year),
        "gridTp": "KRX",
        "pagePath": "/contents/GLB/05/0501/0501110000/GLB0501110000.jsp",
        "code": code,
    }
    if page_first_call:
        data["pageFirstCall"] = "Y"
    response = requests.post(
        "http://global.krx.co.kr/contents/GLB/99/GLB99000001.jspx",
        headers=headers,
        data=data,
    )
    body = response.json()
    return body  # noqa: RET504


def get_precomputed_krx_holidays_online(from_year=None, to_year=None):
    if from_year is None:
        from_year = download_holidays_as_dict_oldest_year_available
    if to_year is None:
        now = pd.Timestamp.now("Asia/Seoul")
        to_year = now.year
    years = range(from_year, to_year + 1)
    precomputed_holidays = []
    for i, year in enumerate(years):
        page_first_call = i == 0
        result = download_krx_holidays_as_dict(year, page_first_call=page_first_call)
        for item in result["block1"]:
            holiday = item["calnd_dd"]
            precomputed_holidays.append(holiday)
    return pd.to_datetime(precomputed_holidays)


def update_dupmed_precomputed_krx_holidays():
    xkrx_holidays_py = Path(__file__).parent / "../exchange_calendars/xkrx_holidays.py"
    with xkrx_holidays_py.open("r") as f:
        lines = list(f)
    start_line = "dumped_precomputed_krx_holidays = pd.DatetimeIndex("
    end_line = ")"
    start_line_index = 0
    end_line_index = 0
    for i, line in enumerate(lines):
        if line.startswith(start_line):
            start_line_index = i + 2
        elif start_line_index > 0 and line.startswith(end_line):
            end_line_index = i - 2
            break
    if start_line_index > 0 and end_line_index > 0:
        precomputed_holidays = get_precomputed_krx_holidays_online()
        precomputed_lines = [
            '        "{}",\n'.format(pd.Timestamp(holiday).strftime("%Y-%m-%d"))
            for holiday in precomputed_holidays
        ]
        replaced_lines = (
            lines[:start_line_index] + precomputed_lines + lines[end_line_index + 1 :]
        )
        with xkrx_holidays_py.open("w") as f:
            f.write("".join(replaced_lines))


if __name__ == "__main__":
    update_dupmed_precomputed_krx_holidays()
