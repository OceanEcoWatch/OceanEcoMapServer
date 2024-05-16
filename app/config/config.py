import os

from dotenv import load_dotenv
from sqlalchemy import URL

from app.config.import_secrets_AWS import get_parameter  # type: ignore

load_dotenv(override=True)


if "DEBUG" in os.environ:

    SENTINAL_HUB = {
        "INSTANCE_ID": os.environ["SH_INSTANCE_ID"],
        "CLIENT_ID": os.environ["SH_CLIENT_ID"],
        "CLIENT_SECRET": os.environ["SH_CLIENT_SECRET"],
    }

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
    print("DEBUG MODE")
    print(DB_USER)
else:  # in Production get the secrets from AWS
    SENTINAL_HUB = {
        "INSTANCE_ID": get_parameter("/fastAPI-backend/SH_INSTANCE_ID"),
        "CLIENT_ID": get_parameter("/fastAPI-backend/SH_CLIENT_ID"),
        "CLIENT_SECRET": get_parameter("/fastAPI-backend/SH_CLIENT_SECRET")
    }
    DB_USER = get_parameter("/fastAPI-backend/DB_USER")
    DB_PW = get_parameter("/fastAPI-backend/DB_PW")
    DB_NAME = get_parameter("/fastAPI-backend/DB_NAME")
    DB_HOST = get_parameter("/fastAPI-backend/DB_HOST")
    DB_PORT = get_parameter("/fastAPI-backend/DB_PORT")
    print("PRODUCTION MODE")
    print(DB_USER)

DEFAULT_MAX_ROW_LIMIT = 1000
DATABASE_URL = URL.create(
    "postgresql",
    username=DB_USER,
    password=DB_PW,  # plain (unescaped) text
    host=DB_HOST,
    database=DB_NAME,
)
