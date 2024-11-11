from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Game Pydantic schema
class GameCreate(BaseModel):
    game_id: str
    rated: bool
    variant: str
    speed: str
    perf: str
    created_at: datetime
    last_move_at: datetime
    status: str
    source: Optional[str]
    winner: Optional[str]
    pgn: Optional[str]
    clock_initial: int
    clock_increment: int
    clock_total_time: int

class Game(BaseModel):
    game_id: str
    rated: bool
    variant: str
    speed: str
    perf: str
    created_at: datetime
    last_move_at: datetime
    status: str
    source: Optional[str]
    winner: Optional[str]
    pgn: Optional[str]
    clock_initial: int
    clock_increment: int
    clock_total_time: int

    class Config:
        orm_mode = True

# Player Pydantic schema
class PlayerCreate(BaseModel):
    lichess_id: str
    name: str
    flair: Optional[str] = None

class Player(BaseModel):
    id: int
    lichess_id: str
    name: str
    flair: Optional[str] = None

    class Config:
        orm_mode = True

# GameMove Pydantic schema
class GameMoveCreate(BaseModel):
    lichess_game_id: str
    move_number: int
    move: str

class GameMove(BaseModel):
    id: int
    lichess_game_id: str
    move_number: int
    move: str

    class Config:
        orm_mode = True

# GamePlayer (Relationship between game and players) Pydantic schema
class GamePlayerCreate(BaseModel):
    lichess_game_id: str
    player_id: int
    color: str
    rating_diff: Optional[int] = None
    rating: int

class GamePlayer(BaseModel):
    lichess_game_id: str
    player_id: int
    color: str
    rating_diff: Optional[int] = None
    rating: int

    class Config:
        orm_mode = True

class LastMoveTimeResponse(BaseModel):
    last_move_time: int # unix time in milliseconds

    class Config:
        orm_mode = True