import datetime
from datetime import timezone


def percent_to_accuracy(percent: int):
    return 255 / 100 * percent


def accuracy_limit_to_percent(accuracy: int):
    return accuracy / 255 * 100


async def get_start_of_day_unix_timestamp(date_time):
    utc = date_time.astimezone(timezone.utc)
    start_of_utc_day = datetime.datetime(
        utc.year, utc.month, utc.day, tzinfo=datetime.timezone.utc
    )
    return start_of_utc_day.timestamp()
