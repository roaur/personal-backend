# fastapi/Dockerfile

# Use the official Python 3.12 image as the base
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY ./fastapi/requirements.txt .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Alembic configuration file
COPY ./fastapi/alembic.ini /app/alembic.ini

# Copy the FastAPI app code and migrations into the container
COPY ./fastapi/app /app/app
COPY ./fastapi/migrations /app/migrations
COPY .env /app/.env

# Expose FastAPI port
EXPOSE 8000

# Command to run Alembic migrations and start FastAPI
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug"]

