"""DateTime utilities for timestamp formatting and timezone handling."""

from datetime import datetime, timezone
from typing import Optional

import pytz
from dateutil import tz


def get_local_timezone(timezone_name: str = "UTC") -> tz.tzinfo:
    """Get timezone object from name.

    Args:
        timezone_name: Timezone name (e.g., "America/New_York", "Europe/London")

    Returns:
        Timezone object

    Raises:
        ValueError: If timezone name is invalid
    """
    try:
        return pytz.timezone(timezone_name)
    except pytz.UnknownTimeZoneError as e:
        raise ValueError(f"Unknown timezone: {timezone_name}") from e


def format_timestamp_for_filename(dt: datetime, include_seconds: bool = True) -> str:
    """Format datetime for use in filenames: YYYY-MM-DD_HH-MM-SS.

    Args:
        dt: Datetime to format
        include_seconds: Whether to include seconds in the output

    Returns:
        Formatted string (e.g., "2026-01-03_14-23-45")
    """
    if include_seconds:
        return dt.strftime("%Y-%m-%d_%H-%M-%S")
    return dt.strftime("%Y-%m-%d_%H-%M")


def format_timestamp_for_header(
    dt: datetime, timezone_name: str = "UTC", format_str: str = "HH:MM"
) -> str:
    """Format datetime for markdown headers.

    Args:
        dt: Datetime to format
        timezone_name: Timezone to convert to
        format_str: Format string (e.g., "HH:MM", "HH:MM:SS")

    Returns:
        Formatted time string (e.g., "14:23")
    """
    local_tz = get_local_timezone(timezone_name)

    # Convert to local timezone if datetime is timezone-aware
    if dt.tzinfo is not None:
        local_dt = dt.astimezone(local_tz)
    else:
        # Assume UTC if no timezone info
        local_dt = dt.replace(tzinfo=timezone.utc).astimezone(local_tz)

    # Convert format string to strftime format
    # HH:MM -> %H:%M
    # HH:MM:SS -> %H:%M:%S
    strftime_format = format_str.replace("HH", "%H").replace("MM", "%M").replace("SS", "%S")

    return local_dt.strftime(strftime_format)


def format_date_for_filename(dt: datetime) -> str:
    """Format datetime for daily markdown filename: YYYY-MM-DD.md.

    Args:
        dt: Datetime to format

    Returns:
        Date string (e.g., "2026-01-03")
    """
    return dt.strftime("%Y-%m-%d")


def parse_telegram_timestamp(timestamp: int) -> datetime:
    """Parse Telegram Unix timestamp to datetime.

    Args:
        timestamp: Unix timestamp from Telegram

    Returns:
        Datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def utcnow() -> datetime:
    """Get current UTC datetime.

    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(timezone.utc)


def to_local_datetime(
    dt: datetime, timezone_name: str = "UTC"
) -> datetime:
    """Convert datetime to local timezone.

    Args:
        dt: Datetime to convert
        timezone_name: Target timezone name

    Returns:
        Datetime in local timezone
    """
    local_tz = get_local_timezone(timezone_name)

    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(local_tz)


def is_same_day(dt1: datetime, dt2: datetime, timezone_name: str = "UTC") -> bool:
    """Check if two datetimes are on the same day in given timezone.

    Args:
        dt1: First datetime
        dt2: Second datetime
        timezone_name: Timezone for comparison

    Returns:
        True if datetimes are on same day
    """
    local1 = to_local_datetime(dt1, timezone_name)
    local2 = to_local_datetime(dt2, timezone_name)

    return (
        local1.year == local2.year
        and local1.month == local2.month
        and local1.day == local2.day
    )
