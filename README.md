## Ocean Plastic Map Server

### Setup

To get started with this project, follow the steps below:
We are using poetry as a dependency manager.

Requirements: Python 3.10 ≤

Install [poetry](https://python-poetry.org/)

- Create a virtual environment and install dependencies using Poetry: `$ poetry install`
- Activate the virtual environment: `$ poetry shell`
- Start the FastAPI server: `$ uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Server is running on http://127.0.0.1:8000
- Access the swagger docs on http://127.0.0.1:8000/docs