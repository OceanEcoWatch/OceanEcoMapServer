
FROM amd64/python:3.11
#python:3.11-bookworm

WORKDIR /code

RUN apt-get update &&\
    apt-get install -y binutils libproj-dev gdal-bin g++ libgdal-dev

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry

# telling poetry to not create a virtualenv
RUN poetry config virtualenvs.create false

COPY ./pyproject.toml /code/./pyproject.toml
# RUN pip install rasterio==1.3.7
RUN poetry install

# Adding environment variables
ENV AWS_DEFAULT_REGION eu-central-1

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
