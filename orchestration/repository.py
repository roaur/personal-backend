from dagster import repository, asset

@asset
def hello_lichess():
    return "Hello, Twins!"

@repository
def lichess_repo():
    return [hello_lichess]