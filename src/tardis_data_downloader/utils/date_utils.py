"""
Date utilities

This module provides date type definitions and conversion utilities
for consistent date handling across the package.
"""

import datetime
from typing import Union, Optional, Literal
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


def date_range(
    start_date: Optional[DATE_TYPE] = None,
    end_date: Optional[DATE_TYPE] = None,
    inclusive: Literal["both", "neither", "left", "right"] = "both",
    to_str: bool = False,
) -> Union[pd.DatetimeIndex, pd.Index]:
    """
    Generate a range of consecutive dates from start_date to end_date.

    Parameters
    ----------
    start_date : DATE_TYPE, optional
        Start date for the range. If None, uses today's date.
    end_date : DATE_TYPE, optional
        End date for the range. If None, uses start_date.
    inclusive : str, default "both"
        Include boundaries in the range:
        - "both": Include both start and end dates
        - "neither": Exclude both start and end dates
        - "left": Include start date, exclude end date
        - "right": Exclude start date, include end date
    to_str : bool, default False
        If True, return dates as string in YYYY-MM-DD format

    Returns
    -------
    pd.DatetimeIndex or pd.Index
        Range of consecutive dates

    Raises
    ------
    ValueError
        If start_date > end_date or invalid inclusive value

    Examples
    --------
    >>> date_range("2025-01-01", "2025-01-05")
    DatetimeIndex(['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
                  dtype='datetime64[ns]', name='date', freq='D')

    >>> date_range("2025-01-01", "2025-01-05", inclusive="neither")
    DatetimeIndex(['2025-01-02', '2025-01-03', '2025-01-04'],
                  dtype='datetime64[ns]', name='date', freq='D')

    >>> date_range("2025-01-01", "2025-01-03", to_str=True)
    Index(['2025-01-01', '2025-01-02', '2025-01-03'], dtype='object', name='date')
    """
    # Handle default dates
    if start_date is None:
        start_date = datetime.date.today()
    if end_date is None:
        end_date = start_date

    # Convert to datetime.date for consistent handling
    start_date_parsed = parse_date(start_date)
    end_date_parsed = parse_date(end_date)

    if start_date_parsed is None or end_date_parsed is None:
        raise ValueError("start_date and end_date cannot be None")

    # Validate date range
    if start_date_parsed > end_date_parsed:
        raise ValueError("start_date cannot be after end_date")

    # Validate inclusive parameter
    valid_inclusive = {"both", "neither", "left", "right"}
    if inclusive not in valid_inclusive:
        raise ValueError(
            f"Invalid inclusive value: {inclusive}. Must be one of {valid_inclusive}"
        )

    # Generate date range using pandas
    date_range_series = pd.date_range(
        start=start_date_parsed, end=end_date_parsed, freq="D"
    )

    # Apply inclusive filtering
    if inclusive == "neither":
        # Exclude both boundaries
        if len(date_range_series) >= 2:
            date_range_series = date_range_series[1:-1]
        else:
            date_range_series = pd.DatetimeIndex([], name="date")
    elif inclusive == "left":
        # Include start, exclude end
        if len(date_range_series) >= 1:
            date_range_series = date_range_series[:-1]
        else:
            date_range_series = pd.DatetimeIndex([], name="date")
    elif inclusive == "right":
        # Exclude start, include end
        if len(date_range_series) >= 1:
            date_range_series = date_range_series[1:]
        else:
            date_range_series = pd.DatetimeIndex([], name="date")
    # inclusive == "both" means include everything (default pandas behavior)

    # Convert to string format if requested
    if to_str:
        date_range_series = date_range_series.strftime("%Y-%m-%d")

    return date_range_series.rename("date")


if __name__ == "__main__":
    # python -m src.tardis_data_downloader.utils.date_utils
    print(date_range(to_str=True))
    print(date_range("2025-01-01", "2025-01-05"))
    print(date_range("2025-01-01", to_str=True))
    print(date_range("2025-01-01", "2025-01-01", to_str=True))
    import ipdb

    ipdb.set_trace()
