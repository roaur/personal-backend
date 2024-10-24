from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app import models, schemas

# Create a new game
async def create_game(db: AsyncSession, game: schemas.GameCreate):
    # Convert game to a dict and extract the clock data
    game_data = game.dict()  # This converts the Pydantic model to a dictionary
    clock_data = game_data.pop('clock', None)  # Remove and get the clock object

    # If clock data exists, flatten it into individual fields
    if clock_data:
        game_data['clock_initial'] = clock_data['initial']
        game_data['clock_increment'] = clock_data['increment']
        game_data['clock_total_time'] = clock_data['totalTime']
    db_game = models.Game(**game_data)  # Convert Pydantic model to SQLAlchemy model
    db.add(db_game)
    await db.commit()
    await db.refresh(db_game)
    return db_game

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
