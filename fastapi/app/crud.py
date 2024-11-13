from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func
from app import models, schemas
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

# Create a new game
async def create_game(db: AsyncSession, game: schemas.GameCreate):
    # Convert game to a dict and extract the clock data
    game_data = game.dict()  # This converts the Pydantic model to a dictionary
    game_data = flatten_clock_data(game_data)
    # print(game_data)
    # logger.debug(game_data)

    # Create an upsert statement (insert on conflict)
    stmt = insert(models.Game).values(**game_data).on_conflict_do_update(
        index_elements=['game_id'],  # on game_id conflict do update
        set_=game_data       # Fields to update in case of conflict
                             # basically, all of them
    )

    # Execute the statement
    await db.execute(stmt)
    await db.commit()

    # Fetch the inserted/updated row for returning
    result = await db.execute(
        select(models.Game).filter_by(game_id=game_data['game_id'])
    )
    return result.scalar_one()

# Get a list of games
async def get_games(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(models.Game).offset(skip).limit(limit))
    return result.scalars().all()

# Get players in a game
async def get_players_from_game(db: AsyncSession, lichess_id: str):
    result = await db.execute(select(models.GamePlayer).filter(models.GamePlayer.lichess_game_id == lichess_id))
    return result.scalars().all()

# Create a new player
async def create_player(db: AsyncSession, player: schemas.PlayerCreate):
    db_player = models.Player(**player.dict())
    db.add(db_player)
    await db.commit()
    await db.refresh(db_player)
    return db_player

# Get a player by Lichess ID
async def get_player_by_lichess_id(db: AsyncSession, lichess_id: str):
    result = await db.execute(select(models.Player).filter(models.Player.lichess_id == lichess_id))
    return result.scalars().first()

# Add a move to a game
async def add_move(db: AsyncSession, move: schemas.GameMoveCreate):
    db_move = models.GameMove(**move.dict())
    db.add(db_move)
    await db.commit()
    await db.refresh(db_move)
    return db_move

# Add a player to a game
async def add_player_to_game(db: AsyncSession, game_id: str, player: schemas.GamePlayerCreate):
    db_game_player = models.GamePlayer(**player.dict())
    db.add(db_game_player)
    await db.commit()
    await db.refresh(db_game_player)
    return db_game_player

# Get the most recent lastMoveAt in unix milliseconds from the games table
async def get_last_move_time(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.max(models.Game.last_move_at))  # Get the maximum lastMoveAt
    )
    last_move_time = result.scalar()
    if last_move_time:
        return {"last_move_time": int(last_move_time.timestamp() * 1000)}  # Wrap in a dictionary
    return {"last_move_time": 0}  # Return 0 wrapped in a dictionary