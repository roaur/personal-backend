"""
FastAPI Application Entry Point.

This module defines the API endpoints for the Chess Data Service.
It handles:
1. Game Ingestion (Single & Batch).
2. Player Ingestion (Single & Batch).
3. Orchestration Support (Getting next player, last move time).
4. Data Retrieval (Games, Players).

Dependencies:
- `get_db`: Provides an async database session for each request.
"""

import uvicorn
import sys
from fastapi import FastAPI, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, utils
from common import schemas, database
import logging
import coloredlogs

# =============================================================================
# Logging Setup
# =============================================================================
from typing import Optional

logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(funcName)s %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

logger.info('API is starting up')

app = FastAPI(
    title="Chess Data API",
    description="API for storing and retrieving Lichess game data.",
    version="1.0.0"
)

# =============================================================================
# Dependencies
# =============================================================================

async def get_db():
    """
    Dependency that yields an async database session.
    Ensures the session is closed after the request is finished.
    """
    async with database.AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# =============================================================================
# Game Endpoints
# =============================================================================

@app.post("/games/", response_model=schemas.Game, status_code=status.HTTP_201_CREATED)
async def create_game(game: schemas.GameCreate, db: AsyncSession = Depends(get_db)):
    """Creates or updates a single game."""
    logger.debug(game)
    db_game = await crud.create_game(db, game)
    logger.debug(db_game)
    return db_game

@app.post("/games/batch", response_model=list[schemas.Game], status_code=status.HTTP_201_CREATED)
async def create_games_batch(games: list[schemas.GameCreate], db: AsyncSession = Depends(get_db)):
    """Creates or updates multiple games in a batch."""
    db_games = await crud.create_games_batch(db, games)
    return db_games

@app.get("/games/", response_model=list[schemas.Game])
async def get_games(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retrieves a paginated list of games."""
    games = await crud.get_games(db, skip=skip, limit=limit)
    return games

@app.get("/games/get_last_move_played_time", response_model=schemas.LastMoveTimeResponse)
async def fetch_last_move_time(db: AsyncSession = Depends(get_db)):
    """
    Returns the timestamp of the most recent move in the DB.
    Used by the orchestrator to resume fetching.
    """
    last_move_time = await crud.get_last_move_time(db)
    return last_move_time

@app.get("/games/get_last_move_played_time/{player_id}", response_model=schemas.LastMoveTimeResponse)
async def fetch_last_move_time_for_player(player_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the timestamp of the most recent move for a specific player.
    """
    last_move_time = await crud.get_last_move_time_for_player(db, player_id)
    return {"last_move_time": last_move_time}

@app.post("/games/{game_id}/moves/", response_model=list[schemas.GameMove], status_code=status.HTTP_201_CREATED)
async def add_moves(
    game_id: str,
    moves: schemas.MovesInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Parses and stores moves for a game.
    Input is a space-separated string of SAN moves.
    """
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

# =============================================================================
# Player Endpoints
# =============================================================================

@app.post("/players/", response_model=schemas.Player, status_code=status.HTTP_201_CREATED)
async def create_player(player: schemas.PlayerCreate, db: AsyncSession = Depends(get_db)):
    """Creates or updates a single player."""
    db_player = await crud.create_player(db, player)
    return db_player

@app.post("/players/batch", response_model=list[schemas.Player], status_code=status.HTTP_201_CREATED)
async def create_players_batch(players: list[schemas.PlayerCreate], db: AsyncSession = Depends(get_db)):
    """Creates or updates multiple players in a batch."""
    db_players = await crud.create_players_batch(db, players)
    return db_players

@app.get("/players/process/next", response_model=schemas.PlayerProcessResponse)
async def get_next_player_to_process(db: AsyncSession = Depends(get_db)):
    """
    Orchestrator Endpoint: Returns the next player to fetch games for.
    Uses locking to prevent race conditions.
    """
    db_player = await crud.get_next_player_to_process(db)
    if db_player is None:
        raise HTTPException(status_code=404, detail="No players to process")
    return db_player

@app.put("/players/{player_id}/fetched")
async def update_player_fetched(player_id: str, db: AsyncSession = Depends(get_db)):
    """Updates the last_fetched_at timestamp for a player."""
    await crud.update_player_fetched_at(db, player_id)
    return {"status": "ok"}

@app.get("/players/{lichess_id}", response_model=schemas.Player)
async def get_player(lichess_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a player by Lichess ID."""
    db_player = await crud.get_player_by_lichess_id(db, lichess_id)
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player

# =============================================================================
# Game-Player Link Endpoints
# =============================================================================

@app.post("/games/{game_id}/players/", response_model=schemas.GamePlayer, status_code=status.HTTP_201_CREATED)
async def add_player_to_game(game_id: str, player: schemas.GamePlayerCreate, db: AsyncSession = Depends(get_db)):
    """Links a player to a game."""
    db_game_player = await crud.add_player_to_game(db, game_id, player)
    return db_game_player

@app.post("/games/players/batch", response_model=list[schemas.GamePlayer], status_code=status.HTTP_201_CREATED)
async def add_players_to_games_batch(game_players: list[schemas.GamePlayerCreate], db: AsyncSession = Depends(get_db)):
    """Links multiple players to games in a batch."""
    db_game_players = await crud.add_players_to_games_batch(db, game_players)
    return db_game_players

@app.get("/games/{game_id}/players", response_model=list[schemas.GamePlayer])
async def get_players_from_game(game_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all players for a given game."""
    db_game_players = await crud.get_players_from_game(db, game_id)
    return db_game_players

# =============================================================================
# Analysis Endpoints
# =============================================================================

@app.get("/games/{game_id}/pgn", response_model=dict)
async def get_game_pgn(game_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the PGN for a game."""
    pgn = await crud.get_game_pgn(db, game_id)
    if pgn is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"pgn": pgn}

@app.post("/games/{game_id}/metrics", response_model=schemas.GameMetrics)
async def upsert_game_metrics(game_id: str, metrics: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Upserts analysis metrics for a game."""
    db_metrics = await crud.upsert_game_metrics(db, game_id, metrics)
    return db_metrics

@app.get("/games/{game_id}/metrics", response_model=Optional[schemas.GameMetrics])
async def get_game_metrics(game_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves analysis metrics for a game."""
    db_metrics = await crud.get_game_metrics(db, game_id)
    if db_metrics is None:
        return None
    return db_metrics

@app.post("/games/analysis/queue", response_model=list[str])
async def get_games_needing_analysis(
    plugins: list[str] = Body(...), 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a list of game IDs that need analysis for the specified plugins.
    """
    game_ids = await crud.get_games_needing_analysis(db, plugins, limit)
    return game_ids