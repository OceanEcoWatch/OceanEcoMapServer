import datetime

from pytz import timezone

from app.db.connect import Session


def percent_to_accuracy(percent: int):
    return 255 / 100 * percent


def accuracy_limit_to_percent(accuracy: int):
    return accuracy / 255 * 100


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


async def get_start_of_day_unix_timestamp(date_time):
    utc = date_time.astimezone(timezone.utc)
    start_of_utc_day = datetime.datetime(
        utc.year, utc.month, utc.day, tzinfo=timezone.utc
    )
    return start_of_utc_day.timestamp()
