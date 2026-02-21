from datetime import datetime

def format_date(date: datetime) -> str:
    """
    Formats a datetime object into a human-readable string format.

    Args:
        date (datetime): The datetime object to format.

    Returns:
        str: The formatted date string in the format 'YYYY-MM-DD'.
    """
    return date.strftime('%Y-%m-%d')