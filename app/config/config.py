import os

from dotenv import load_dotenv
from sqlalchemy import URL  # type: ignore

load_dotenv(override=True)

# Check if DB_URL exists
if "DB_URL" in os.environ:
    DATABASE_URL = os.environ["DB_URL"]
else:
    DB_USER = os.environ["DB_USER"]
    DB_PW = os.environ["DB_PW"]
    DB_NAME = os.environ["DB_NAME"]
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = os.environ["DB_PORT"]

    DATABASE_URL = URL.create(
        "postgresql",
        username=DB_USER,
        password=DB_PW,  # plain (unescaped) text
        host=DB_HOST,
        database=DB_NAME,
    )

DEFAULT_MAX_ROW_LIMIT = 1000
