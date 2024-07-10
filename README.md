# OEW Backend

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
