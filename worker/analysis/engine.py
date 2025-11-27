import duckdb
import logging
import pandas as pd
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DuckDBEngine:
    """
    Wrapper around DuckDB to handle connections and query execution.
    Designed to be used within Celery tasks.
    """
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establishes a connection to the DuckDB instance."""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise

    def close(self):
        """Closes the connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("DuckDB connection closed")

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Any]:
        """
        Executes a SQL query and returns the result as a list of tuples.
        """
        if not self.conn:
            self.connect()
        
        try:
            if params:
                return self.conn.execute(query, params).fetchall()
            else:
                return self.conn.execute(query).fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            raise

    def query_df(self, query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """
        Executes a SQL query and returns the result as a Pandas DataFrame.
        """
        if not self.conn:
            self.connect()
            
        try:
            if params:
                return self.conn.execute(query, params).df()
            else:
                return self.conn.execute(query).df()
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            raise

    def register_df(self, name: str, df: pd.DataFrame):
        """
        Registers a Pandas DataFrame as a virtual table in DuckDB.
        """
        if not self.conn:
            self.connect()
            
        try:
            self.conn.register(name, df)
            logger.info(f"Registered DataFrame as table '{name}'")
        except Exception as e:
            logger.error(f"Failed to register DataFrame: {e}")
            raise
