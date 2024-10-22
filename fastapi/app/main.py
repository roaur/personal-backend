from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, database

app = FastAPI()

# Dependency to get a database session
async def get_db():
    async with database.AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# Endpoint to create a new game
@app.post("/games/", response_model=schemas.Game)
async def create_game(game: schemas.GameCreate, db: AsyncSession = Depends(get_db)):
    db_game = await crud.create_game(db, game)
    return db_game

# Endpoint to get a list of games
@app.get("/games/", response_model=list[schemas.Game])
async def get_games(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    games = await crud.get_games(db, skip=skip, limit=limit)
    return games

# Endpoint to create a new player
@app.post("/players/", response_model=schemas.Player)
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

# Endpoint to add a move to a game
@app.post("/games/{game_id}/moves/", response_model=schemas.GameMove)
async def add_move(game_id: str, move: schemas.GameMoveCreate, db: AsyncSession = Depends(get_db)):
    db_move = await crud.add_move(db, move)
    return db_move

# Endpoint to add a player to a game
@app.post("/games/{game_id}/players/", response_model=schemas.GamePlayer)
async def add_player_to_game(game_id: str, player: schemas.GamePlayerCreate, db: AsyncSession = Depends(get_db)):
    db_game_player = await crud.add_player_to_game(db, game_id, player)
    return db_game_player

# Endpoint to get players from a game
@app.get("/players/{game_id}", response_model=list[schemas.GamePlayer])
async def get_players_from_game(game_id: str, db: AsyncSession = Depends(get_db)):
    db_game_players = await crud.get_players_from_game(db, game_id)
    return db_game_players

## TODO: Add endpoints that combine writing a game and players (or searching for players in the db)
## TODO: Handle incoming game PGNs. Split the records somehow to write to GameMove