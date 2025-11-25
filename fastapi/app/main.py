import uvicorn
import sys
from fastapi import FastAPI, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, database, utils

import logging

# logger = logging.getLogger('uvicorn.error')
# http_logger = logging.getLogger('uvicorn.access')


# logger.debug("FastAPI application starting...")
app = FastAPI()
# logger.debug("FastAPI application started!")

import coloredlogs

logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)
# logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(funcName)s %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)

# logger.addHandler(stream_handler)
logger.addHandler(file_handler)

logger.info('API is starting up')

# Dependency to get a database session
async def get_db():
    async with database.AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# Endpoint to create a new game
@app.post("/games/", response_model=schemas.Game, status_code=status.HTTP_201_CREATED)
async def create_game(game: schemas.GameCreate, db: AsyncSession = Depends(get_db)):
    logger.debug(game)
    db_game = await crud.create_game(db, game)
    logger.debug(db_game)
    return db_game

# Endpoint to get a list of games
@app.get("/games/", response_model=list[schemas.Game])
async def get_games(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    games = await crud.get_games(db, skip=skip, limit=limit)
    return games

# Endpoint to create a new player
@app.post("/players/", response_model=schemas.Player, status_code=status.HTTP_201_CREATED)
async def create_player(player: schemas.PlayerCreate, db: AsyncSession = Depends(get_db)):
    db_player = await crud.create_player(db, player)
    return db_player

# Endpoint to get a player by Lichess ID
@app.get("/players/{lichess_id}", response_model=schemas.Player)
async def get_player(lichess_id: str, db: AsyncSession = Depends(get_db)):
    db_player = await crud.get_player_by_lichess_id(db, lichess_id)
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player

# Endpoint to add moves to a game
@app.post("/games/{game_id}/moves/", response_model=list[schemas.GameMove], status_code=status.HTTP_201_CREATED)
async def add_moves(
    game_id: str,
    moves: schemas.MovesInput,  # Example input for docs
    db: AsyncSession = Depends(get_db),
):
    game_moves = moves.model_dump()
    move_list = game_moves.get("moves", "").split()
    variant = game_moves.get("variant", "standard")
    initial_fen = game_moves.get("initial_fen")
    try:
        enumerated_moves = utils.parse_and_enumerate_moves(game_id, move_list, variant, initial_fen)
        db_move = await crud.add_moves(db, game_id, enumerated_moves)
        return db_move
    except ValueError as e:
        logger.warning(f"Skipping game {game_id} due to invalid move: {e}")
        return []

# Endpoint to add a player to a game
@app.post("/games/{game_id}/players/", response_model=schemas.GamePlayer, status_code=status.HTTP_201_CREATED)
async def add_player_to_game(game_id: str, player: schemas.GamePlayerCreate, db: AsyncSession = Depends(get_db)):
    db_game_player = await crud.add_player_to_game(db, game_id, player)
    return db_game_player

# Endpoint to get players from a game
@app.get("/players/{game_id}", response_model=list[schemas.GamePlayer])
async def get_players_from_game(game_id: str, db: AsyncSession = Depends(get_db)):
    db_game_players = await crud.get_players_from_game(db, game_id)
    return db_game_players

# Endpoint to get the last move from the games table
@app.get("/games/get_last_move_played_time", response_model=schemas.LastMoveTimeResponse)
async def fetch_last_move_time(db: AsyncSession = Depends(get_db)):
    last_move_time = await crud.get_last_move_time(db)
    # Note: this will return 0 if there is no last move time
    return last_move_time

## TODO: Add endpoints that combine writing a game and players (or searching for players in the db)
## TODO: Handle incoming game PGNs. Split the records somehow to write to GameMove