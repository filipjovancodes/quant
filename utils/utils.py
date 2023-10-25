from datetime import datetime


def format_date(date: datetime) -> str:
    output = str(date.year)
    m = str(date.month)
    if len(m) == 1:
        m = "0" + m
    output += m
    d = str(date.day)
    if len(d) == 1:
        d = "0" + d
    output += d

    return output

def format_datetime(date: str) -> datetime:
    return datetime(year = int(date[0:4]), month = int(date[5:7]), day = int(date[8:10]))

def format_percentage(percent: str) -> float:
        percent = percent.removesuffix("%")
        return float(percent)/100