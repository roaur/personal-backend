# FROM apache/airflow:2.6.1-python3.8
FROM apache/airflow:slim-latest-python3.12

# Set Airflow user
USER airflow

# Set environment variables
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

# Copy airflow requirements
COPY ./airflow/requirements.txt .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the DAGs and utils
COPY ./airflow/dags /opt/airflow/dags/
COPY ./airflow/utils /opt/airflow/utils/

# Set working directory
WORKDIR /opt/airflow
