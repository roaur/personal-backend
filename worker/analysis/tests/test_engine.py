import pytest
import pandas as pd
from worker.analysis.engine import DuckDBEngine

def test_connection():
    engine = DuckDBEngine()
    engine.connect()
    assert engine.conn is not None
    engine.close()
    assert engine.conn is None

def test_execute_query():
    engine = DuckDBEngine()
    engine.connect()
    result = engine.execute_query("SELECT 1 + 1")
    assert result == [(2,)]
    engine.close()

def test_query_df():
    engine = DuckDBEngine()
    engine.connect()
    df = engine.query_df("SELECT 1 AS a, 2 AS b")
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]['a'] == 1
    assert df.iloc[0]['b'] == 2
    engine.close()

def test_register_df():
    engine = DuckDBEngine()
    df_input = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
    
    engine.register_df('my_table', df_input)
    
    result_df = engine.query_df("SELECT * FROM my_table WHERE x > 1")
    assert len(result_df) == 2
    assert result_df.iloc[0]['x'] == 2
    engine.close()
