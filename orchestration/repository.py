from dagster import repository, asset

@asset
def hello_lichess():
    return "Hello, Twins!"

from orchestration.assets.analytics import analytic_assets

@repository
def lichess_repo():
    return [hello_lichess, *analytic_assets]