FROM apache/airflow:2.6.1-python3.8

# Set Airflow user
USER airflow

# Set environment variables
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

# Copy the DAGs and utils
COPY ./dags /opt/airflow/dags/
COPY ./utils /opt/airflow/utils/

# Set working directory
WORKDIR /opt/airflow
