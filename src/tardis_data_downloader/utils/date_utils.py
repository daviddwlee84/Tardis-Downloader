"""
Date utilities for the SyntheticSnapshot package.

This module provides date type definitions and conversion utilities
for consistent date handling across the package.
"""

import datetime
from typing import Union, Optional
import pandas as pd

# Date type definition - supports various date formats
DATE_TYPE = Union[str, datetime.date, datetime.datetime, pd.Timestamp, None]


def to_date_string(date: DATE_TYPE) -> Optional[str]:
    """
    Convert various date types to ISO format date string (YYYY-MM-DD).

    Parameters
    ----------
    date : DATE_TYPE
        Date in various formats:
        - str: Expected in YYYY-MM-DD format (returned as-is if valid)
        - datetime.date: Converted to ISO format
        - datetime.datetime: Date part extracted and converted to ISO format
        - pd.Timestamp: Date part extracted and converted to ISO format
        - None: Returns None

    Returns
    -------
    str or None
        Date string in YYYY-MM-DD format, or None if input is None

    Raises
    ------
    ValueError
        If the input date type is not supported or string format is invalid

    Examples
    --------
    >>> to_date_string("2025-08-04")
    '2025-08-04'

    >>> to_date_string(datetime.date(2025, 8, 4))
    '2025-08-04'

    >>> to_date_string(datetime.datetime(2025, 8, 4, 14, 30))
    '2025-08-04'

    >>> to_date_string(pd.Timestamp('2025-08-04'))
    '2025-08-04'

    >>> to_date_string(None)
    None
    """
    if date is None:
        return None

    if isinstance(date, str):
        # Validate string format and return as-is if valid
        try:
            # Try to parse the string to validate format
            datetime.datetime.strptime(date, "%Y-%m-%d")
            return date
        except ValueError:
            # Try other common formats
            try:
                # Try YYYYMMDD format
                parsed = datetime.datetime.strptime(date, "%Y%m%d")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Try YYYY/MM/DD format
                    parsed = datetime.datetime.strptime(date, "%Y/%m/%d")
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    raise ValueError(
                        f"Invalid date string format: {date}. Expected YYYY-MM-DD, YYYYMMDD, or YYYY/MM/DD"
                    )

    elif isinstance(date, datetime.date):
        return date.isoformat()

    elif isinstance(date, datetime.datetime):
        return date.date().isoformat()

    elif isinstance(date, pd.Timestamp):
        return date.date().isoformat()

    else:
        raise ValueError(
            f"Unsupported date type: {type(date)}. Expected str, datetime.date, datetime.datetime, pd.Timestamp, or None"
        )


def validate_date_format(date_str: str) -> bool:
    """
    Validate if a date string is in the correct YYYY-MM-DD format.

    Parameters
    ----------
    date_str : str
        Date string to validate

    Returns
    -------
    bool
        True if the date string is valid and in YYYY-MM-DD format

    Examples
    --------
    >>> validate_date_format("2025-08-04")
    True

    >>> validate_date_format("25-08-04")
    False

    >>> validate_date_format("2025/08/04")
    False
    """
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def parse_date(date: DATE_TYPE) -> Optional[datetime.date]:
    """
    Parse various date types to datetime.date object.

    Parameters
    ----------
    date : DATE_TYPE
        Date in various formats

    Returns
    -------
    datetime.date or None
        Parsed date object, or None if input is None

    Examples
    --------
    >>> parse_date("2025-08-04")
    datetime.date(2025, 8, 4)

    >>> parse_date(datetime.datetime(2025, 8, 4, 14, 30))
    datetime.date(2025, 8, 4)
    """
    if date is None:
        return None

    if isinstance(date, str):
        date_str = to_date_string(date)  # This will handle format conversion
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    elif isinstance(date, datetime.date):
        return date

    elif isinstance(date, datetime.datetime):
        return date.date()

    elif isinstance(date, pd.Timestamp):
        return date.date()

    else:
        raise ValueError(f"Unsupported date type: {type(date)}")


def get_today_string() -> str:
    """
    Get today's date as a string in YYYY-MM-DD format.

    Returns
    -------
    str
        Today's date in YYYY-MM-DD format

    Examples
    --------
    >>> get_today_string()  # doctest: +SKIP
    '2025-08-07'
    """
    return datetime.date.today().isoformat()


def format_date_range(start_date: DATE_TYPE, end_date: DATE_TYPE) -> tuple[str, str]:
    """
    Format a date range to string tuple.

    Parameters
    ----------
    start_date : DATE_TYPE
        Start date
    end_date : DATE_TYPE
        End date

    Returns
    -------
    tuple[str, str]
        Formatted start and end dates

    Examples
    --------
    >>> format_date_range("2025-08-01", "2025-08-07")
    ('2025-08-01', '2025-08-07')
    """
    start_str = to_date_string(start_date)
    end_str = to_date_string(end_date)

    if start_str is None or end_str is None:
        raise ValueError("Both start_date and end_date must be provided")

    return start_str, end_str
