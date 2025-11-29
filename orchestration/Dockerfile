FROM python:3.12-slim

# Install system dependencies (for psycopg2, etc)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/dagster/app

# Install Dagster dependencies
RUN pip install dagster dagster-webserver dagster-postgres dagster-docker psycopg

# Copy your code
COPY . .

# Set generic environment variables
ENV DAGSTER_HOME=/opt/dagster/dagster_home
RUN mkdir -p $DAGSTER_HOME
COPY orchestration/dagster.yaml $DAGSTER_HOME/dagster.yaml

COPY orchestration/init_db.py /opt/dagster/app/init_db.py

WORKDIR /opt/dagster/app