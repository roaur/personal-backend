"""
CRUD Operations (Create, Read, Update, Delete).

This module contains the business logic for interacting with the database.
It uses SQLAlchemy AsyncSession for asynchronous DB operations.

Key Patterns:
- Upserts: Most 'create' operations are actually 'upserts' (Insert on Conflict Update).
  This ensures idempotency: if we process the same game twice, we just update it.
- Batching: Functions ending in `_batch` handle multiple records efficiently.
- Locking: `get_next_player_to_process` uses `SKIP LOCKED` to safely coordinate multiple workers.
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func, or_
from app import models, schemas
from datetime import datetime, timedelta, timezone
from app.data_transformers import flatten_clock_data
from app.utils import json_serializer
import sys
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# =============================================================================
# Game Operations
# =============================================================================

async def create_game(db: AsyncSession, game: schemas.GameCreate):
    """
    Creates or Updates (Upsert) a single game.
    
    Args:
        db: Database session.
        game: Game data (Pydantic model).
        
    Returns:
        The created/updated Game ORM object.
    """
    # Convert game to a dict and extract the clock data
    game_data = game.dict()  # This converts the Pydantic model to a dictionary
    game_data = flatten_clock_data(game_data)

    # Create an upsert statement (insert on conflict)
    # If game_id exists, update all fields.
    stmt = insert(models.Game).values(**game_data).on_conflict_do_update(
        index_elements=['game_id'],  # on game_id conflict do update
        set_=game_data       # Fields to update in case of conflict
    )

    # Execute the statement
    await db.execute(stmt)
    await db.commit()

    # Fetch the inserted/updated row for returning
    result = await db.execute(
        select(models.Game).filter_by(game_id=game_data['game_id'])
    )
    return result.scalar_one()

async def create_games_batch(db: AsyncSession, games: list[schemas.GameCreate]):
    """
    Batch Upsert for games.
    Efficiently inserts multiple games in a single query.
    """
    if not games:
        return []
    
    # Prepare data
    games_data = []
    for game in games:
        g_data = game.dict()
        g_data = flatten_clock_data(g_data)
        games_data.append(g_data)

    # Upsert statement
    stmt = insert(models.Game).values(games_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=['game_id'],
        set_={col.name: stmt.excluded[col.name] for col in models.Game.__table__.columns}
    )

    await db.execute(stmt)
    await db.commit()
    
    # Return inserted games
    game_ids = [g['game_id'] for g in games_data]
    result = await db.execute(select(models.Game).where(models.Game.game_id.in_(game_ids)))
    return result.scalars().all()

async def get_games(db: AsyncSession, skip: int = 0, limit: int = 10):
    """Fetches a paginated list of games."""
    result = await db.execute(select(models.Game).offset(skip).limit(limit))
    return result.scalars().all()

async def get_players_from_game(db: AsyncSession, lichess_id: str):
    """Fetches all players associated with a specific game ID."""
    result = await db.execute(select(models.GamePlayer).filter(models.GamePlayer.lichess_game_id == lichess_id))
    return result.scalars().all()

# =============================================================================
# Player Operations
# =============================================================================

async def create_player(db: AsyncSession, player: schemas.PlayerCreate):
    """
    Creates or Updates (Upsert) a player.
    
    Important: Does NOT update `last_fetched_at` if the player already exists,
    to preserve the crawling state.
    """
    player_data = player.model_dump(exclude_unset=True)
    
    stmt = insert(models.Player).values(**player_data)
    
    # Exclude last_fetched_at from update to prevent resetting it to None
    update_data = {k: v for k, v in player_data.items() if k != 'last_fetched_at'}
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['player_id'],
        set_=update_data
    )
    await db.execute(stmt)
    await db.commit()

    result = await db.execute(
        select(models.Player).filter_by(player_id=player_data['player_id'])
    )
    return result.scalar_one()

async def create_players_batch(db: AsyncSession, players: list[schemas.PlayerCreate]):
    """Batch Upsert for players."""
    if not players:
        return []

    players_data = [p.model_dump(exclude_unset=True) for p in players]
    
    stmt = insert(models.Player).values(players_data)
    
    # Exclude last_fetched_at from update
    update_data = {col.name: stmt.excluded[col.name] for col in models.Player.__table__.columns if col.name != 'last_fetched_at'}

    stmt = stmt.on_conflict_do_update(
        index_elements=['player_id'],
        set_=update_data
    )

    await db.execute(stmt)
    await db.commit()

    player_ids = [p['player_id'] for p in players_data]
    result = await db.execute(select(models.Player).where(models.Player.player_id.in_(player_ids)))
    return result.scalars().all()

async def get_next_player_to_process(db: AsyncSession):
    """
    Orchestrator Logic: Finds the next player to fetch games for.
    
    Selection Criteria:
    1. Depth <= 1 (Main user or immediate opponents).
    2. Has NOT been fetched in the last 24 hours.
    
    Concurrency Safety:
    Uses `FOR UPDATE SKIP LOCKED` to ensure that if multiple orchestrators run,
    they don't pick the same player.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Select with SKIP LOCKED to prevent race conditions
    stmt = select(models.Player).where(
        (models.Player.depth <= 1) &
        (
            (models.Player.last_fetched_at == None) |
            (models.Player.last_fetched_at < cutoff)
        )
    ).order_by(models.Player.last_fetched_at.asc().nullsfirst()).limit(1).with_for_update(skip_locked=True)
    
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if player:
        # Capture original time for the cursor
        original_last_fetched_at = player.last_fetched_at

        # Immediately mark as fetched (temporarily) to prevent others from picking it up
        # This acts as a "claim" on the task.
        player.last_fetched_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(player)
        
        # Restore original time on the object so the worker gets the correct cursor
        # (The worker needs to know when we LAST fetched to only get new games)
        player.last_fetched_at = original_last_fetched_at
    
    return player

async def update_player_fetched_at(db: AsyncSession, player_id: str):
    """Updates the last_fetched_at timestamp for a player to NOW."""
    stmt = update(models.Player).where(models.Player.player_id == player_id).values(
        last_fetched_at=datetime.now(timezone.utc)
    )
    await db.execute(stmt)
    await db.commit()

async def get_player_by_lichess_id(db: AsyncSession, lichess_id: str):
    """Fetches a player by ID."""
    result = await db.execute(select(models.Player).filter(models.Player.lichess_id == lichess_id))
    return result.scalars().first()

# =============================================================================
# Move & Link Operations
# =============================================================================

async def add_moves(db: AsyncSession, game_id: str, moves: list[dict]):
    """
    Bulk insert moves for a game.
    """
    # Map each move dictionary to the model
    db_moves = [models.GameMove(**move) for move in moves]
    
    db.add_all(db_moves)
    await db.commit()
    return db_moves

async def add_player_to_game(db: AsyncSession, game_id: str, player: schemas.GamePlayerCreate):
    """
    Links a player to a game (Insert on Conflict Do Nothing).
    """
    player_data = player.model_dump() # convert to dict
    statement = insert(models.GamePlayer).values(**player_data).on_conflict_do_nothing(
        index_elements=['game_id','player_id']
    )
    await db.execute(statement)
    await db.commit()

    result = await db.execute(
        select(models.GamePlayer).where( # where is more verbose than filter_by
            models.GamePlayer.game_id == player_data['game_id'],
            models.GamePlayer.player_id == player_data['player_id']
        )
    )

    db_game_player = result.scalar_one_or_none()
    return db_game_player

async def add_players_to_games_batch(db: AsyncSession, game_players: list[schemas.GamePlayerCreate]):
    """Batch link players to games."""
    if not game_players:
        return []

    data = [gp.model_dump() for gp in game_players]
    
    stmt = insert(models.GamePlayer).values(data)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['game_id', 'player_id']
    )

    await db.execute(stmt)
    await db.commit()
    
    return [models.GamePlayer(**d) for d in data]

async def get_last_move_time(db: AsyncSession) -> int:
    """
    Gets the timestamp of the most recent move in the database.
    Used by the orchestrator to determine where to resume fetching for the main user.
    """
    result = await db.execute(
        select(func.max(models.Game.last_move_at))  # Get the maximum lastMoveAt
    )
    last_move_time = result.scalar()
    if last_move_time:
        return {"last_move_time": int(last_move_time.timestamp() * 1000)}  # Wrap in a dictionary
    return {"last_move_time": 0}  # Return 0 wrapped in a dictionary