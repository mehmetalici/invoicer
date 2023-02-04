from datetime import datetime
from dateutil import parser
from babel.numbers import format_currency


def get_short_date(date: str):
    parsed = parser.parse(date)
    return parsed.strftime("%d.%m.%Y")


def get_year(date: str):
    return parser.parse(date).year


def eur(value: float):
    return format_currency(value, "EUR", locale="de_DE")