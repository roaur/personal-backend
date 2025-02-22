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
    player_data = player.model_dump()
    statement = insert(models.Player).values(**player_data).on_conflict_do_nothing(
        index_elements=['player_id']
    )
    await db.execute(statement)
    await db.commit()

    result = await db.execute(
        select(models.Player).filter_by(player_id=player_data['player_id'])
    )
    return result.scalar_one()


# Get a player by Lichess ID
async def get_player_by_lichess_id(db: AsyncSession, lichess_id: str):
    result = await db.execute(select(models.Player).filter(models.Player.lichess_id == lichess_id))
    return result.scalars().first()

# # Add a move to a game
# async def add_move(db: AsyncSession, move: schemas.GameMoveCreate):
#     db_move = models.GameMove(**move.dict())
#     db.add(db_move)
#     await db.commit()
#     await db.refresh(db_move)
#     return db_move

# Add multiple moves to a game
async def add_moves(db: AsyncSession, game_id: str, moves: list[dict]):
    """
    Bulk insert moves for a game.
    """
    # Map each move dictionary to the model
    db_moves = [models.GameMove(**move) for move in moves]
    
    db.add_all(db_moves)
    await db.commit()
    return db_moves

# # Add a player to a game
# async def add_player_to_game(db: AsyncSession, game_id: str, player: schemas.GamePlayerCreate):
#     db_game_player = models.GamePlayer(**player.dict())
#     db.add(db_game_player)
#     await db.commit()
#     await db.refresh(db_game_player)
#     return db_game_player

# Add a player to a game
async def add_player_to_game(db: AsyncSession, game_id: str, player: schemas.GamePlayerCreate):
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

# Get the most recent lastMoveAt in unix milliseconds from the games table
async def get_last_move_time(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.max(models.Game.last_move_at))  # Get the maximum lastMoveAt
    )
    last_move_time = result.scalar()
    if last_move_time:
        return {"last_move_time": int(last_move_time.timestamp() * 1000)}  # Wrap in a dictionary
    return {"last_move_time": 0}  # Return 0 wrapped in a dictionary

# Get the most recent lastMoveAt per player
async def get_last_move_time_per_player(db: AsyncSession) -> dict:
    result = await db.execute(
        select(models.GamePlayer.player_id, 
               func.max(models.Game.last_move_at).label("last_move_at")
        )
        .join(models.Game, models.Game.game_id == models.GamePlayer.game_id)
        .group_by(models.GamePlayer.player_id)
    )
    last_move_times = result.all()

    # return a dict for all player last move times
    # if they don't have one dive 0 as their last move time.
    return {
        player_id: int(last_move_time.timestamp() * 1000) if last_move_time else 0
        for player_id, last_move_time in last_move_times
    }