# Ocean Eco Watch Backend

Yayyy! You found the Ocean Eco Watch backend! Here you find a FAST-API backend which main purpose it is to serve data from the DB to the [Frontend Map Application](https://github.com/OceanEcoWatch/OceanEcoWatchMap/tree/main#).

## Environment Variables

```
# DATABASE
DB_USER="your_user"
DB_PW="your_password"
DB_NAME="your_db"
DB_HOST="your_host"
DB_PORT="your_port"

# SENTINEL HUB

SH_INSTANCE_ID="your_instance_id"
SH_CLIENT_ID="your_client_id"
SH_CLIENT_SECRET="your_client_secret"
DEBUG="TRUE/FALSE"

# AWS
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="you_aws_secret"
GITHUB_TOKEN="your_github_token"

```

## Local Setup

### Requirements:

- Python >= 3.10
- DB access (or local copy of it) (see .env.sample)

### Getting Started

1. Install [poetry](https://python-poetry.org/)
2. Create a virtual environment and install dependencies using Poetry: `$ poetry install`
3. Activate the virtual environment: `$ poetry shell`
4. Start the FastAPI server: `$ uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

---`
The Server is now running on http://localhost:8000. You can access the swagger docs on http://127.0.0.1:8000/docs

Type "deactivate" to close the poetry shell.
