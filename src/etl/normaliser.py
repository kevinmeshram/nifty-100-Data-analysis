"""Normalisers: turn many spellings of a year or a ticker into one standard form."""
import re
from datetime import date, datetime

import pandas as pd

MIN_YEAR = 1990
MAX_YEAR = 2100

MONTHS = {
    "JAN": 1, "JANUARY": 1, "FEB": 2, "FEBRUARY": 2, "MAR": 3, "MARCH": 3,
    "APR": 4, "APRIL": 4, "MAY": 5, "JUN": 6, "JUNE": 6, "JUL": 7, "JULY": 7,
    "AUG": 8, "AUGUST": 8, "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
    "OCT": 10, "OCTOBER": 10, "NOV": 11, "NOVEMBER": 11,
    "DEC": 12, "DECEMBER": 12,
}


def _check_year(year):
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError(f"year {year} is outside {MIN_YEAR}-{MAX_YEAR}")
    return year


def _fiscal_year(month, year):
    """Fiscal year ends in March. Jan-Mar stay in the same year. Apr-Dec move up."""
    return year if month <= 3 else year + 1


def _four_digit(token):
    """Convert '23' to 2023. Keep '2023' as 2023."""
    return 2000 + int(token) if len(token) == 2 else int(token)


def normalize_year(value):
    """Return the fiscal year-end as an int, None if missing, ValueError if invalid."""
    if value is None or (not isinstance(value, (list, tuple)) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        raise ValueError(f"not a year: {value!r}")
    if isinstance(value, (datetime, date)):
        return _check_year(_fiscal_year(value.month, value.year))
    if isinstance(value, (int, float)):
        if float(value) != int(value):
            raise ValueError(f"not a whole year: {value!r}")
        return _check_year(int(value))

    clean = str(value).strip().upper()
    if not clean:
        return None

    # Remove a FY prefix. Remember that it was there.
    without_fy = re.sub(r"^F\.?Y\.?\s*[-']?\s*", "", clean)
    had_fy = without_fy != clean
    clean = without_fy

    match = re.fullmatch(r"(\d{4})(?:\.0+)?", clean)
    if match:
        return _check_year(int(match.group(1)))

    if had_fy:
        match = re.fullmatch(r"\d{2}", clean)
        if match:
            return _check_year(2000 + int(clean))

    match = re.fullmatch(r"(\d{4})\s*[-/]\s*(\d{4}|\d{2})", clean)
    if match:
        start = int(match.group(1))
        end = _four_digit(match.group(2)) if len(match.group(2)) == 2 else int(match.group(2))
        if len(match.group(2)) == 2:
            end = start // 100 * 100 + int(match.group(2))
        if end != start + 1:
            raise ValueError(f"years are not in a row: {value!r}")
        return _check_year(end)

    match = re.fullmatch(r"([A-Z]{3,9})[\s\-']*(\d{4}|\d{2})", clean)
    if match and match.group(1) in MONTHS:
        month = MONTHS[match.group(1)]
        return _check_year(_fiscal_year(month, _four_digit(match.group(2))))

    raise ValueError(f"cannot read year: {value!r}")


def normalize_ticker(value):
    """Return an upper-case symbol with no spaces, prefix, or suffix.

    None if missing. ValueError if invalid characters remain.
    """
    if value is None or pd.isna(value):
        return None
    clean = re.sub(r"\s+", "", str(value)).upper()
    if not clean:
        return None
    clean = re.sub(r"^(NSE|BSE):", "", clean)
    clean = re.sub(r"\.(NS|NSE|BO|BSE)$", "", clean)
    if not re.fullmatch(r"[A-Z0-9&\-]+", clean):
        raise ValueError(f"invalid ticker: {value!r}")
    return clean