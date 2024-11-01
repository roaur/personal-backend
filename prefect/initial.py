from prefect import flow, task
import httpx
from datetime import datetime, timedelta
from config import settings  # Import the Pydantic settings
import berserk
    
@task
def fetch_matches(client: berserk.Client, username, num_matches: int = 20):
    matches = client.games.export_by_player(
        username=username,
        as_pgn=False,
        pgn_in_json=True,
        moves=True,
        perf_type='bullet,rapid,blitz,classical',
        max=num_matches,
    )
    return matches

@task
def setup_berserk_client(token) -> berserk.Client:
    session = berserk.TokenSession(token)
    lichess_client = berserk.Client(session)
    return lichess_client

@task
def process_matches(matches):
    # Placeholder for processing logic, such as inserting into a database
    print(f"Fetched {len(matches)} matches")
    # Here you would process and store each match

@task
def match_iterator(matches):
    for match in matches:
        print(match)

@flow
def fetch_lichess_matches():
    client = setup_berserk_client(settings.lichess_token)
    # Use settings to retrieve username and token
    matches = fetch_matches(client, settings.lichess_username)
    # process_matches(matches)
    match_iterator(matches)

# Run the flow
if __name__ == "__main__":
    fetch_lichess_matches()
