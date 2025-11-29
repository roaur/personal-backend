# orchestration/init_db.py
import os
import time
import psycopg  # This is the "psycopg" v3 package, not "psycopg2"
from psycopg.errors import OperationalError

def create_dagster_db():
    target_db = "dagster"
    
    # Connection details from environment
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    host = "postgres"  # Service name in Docker Compose
    
    # Retry loop
    retries = 10
    while retries > 0:
        try:
            # Psycopg 3: Connect with autocommit=True directly
            # We connect to the default 'postgres' db to issue CREATE DATABASE
            with psycopg.connect(
                host=host,
                user=user,
                password=password,
                dbname="postgres",
                autocommit=True 
            ) as conn:
                
                # Psycopg 3: 'execute' returns the cursor, so we can chain
                # Check if DB exists
                res = conn.execute(
                    "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                    (target_db,)
                ).fetchone()

                if not res:
                    print(f"Database '{target_db}' not found. Creating...")
                    # Warning: Parametrized queries cannot be used for identifiers (db names)
                    # We use strict f-string here assuming target_db is trusted/internal string
                    conn.execute(f"CREATE DATABASE {target_db}")
                    print(f"Database '{target_db}' created successfully.")
                else:
                    print(f"Database '{target_db}' already exists. Skipping.")
            
            return # Success

        except OperationalError as e:
            print(f"Waiting for Postgres to accept connections... ({e})")
            time.sleep(2)
            retries -= 1
    
    raise Exception("Could not connect to Postgres after multiple retries.")

if __name__ == "__main__":
    create_dagster_db()