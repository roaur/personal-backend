from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Game Pydantic schema
class Clock(BaseModel):
    initial: int
    increment: int
    total_time: int

class GameCreate(BaseModel):
    game_id: str
    rated: bool
    variant: str
    speed: str
    perf: str
    created_at: datetime
    last_move_at: datetime
    status: str
    source: str
    winner: Optional[str] = None
    pgn: Optional[str] = None
    clock: Clock  # Keep clock as a nested object

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
    player_id: str
    name: str
    flair: Optional[str] = None

class Player(BaseModel):
    player_id: str
    name: str
    flair: Optional[str] = None

    class Config:
        orm_mode = True

class GameMove(BaseModel):
    id: int
    game_id: str
    move_number: int
    move: str

    class Config:
        orm_mode = True

# Schema for a list of moves
class MovesInput(BaseModel):
    moves: str = Field(
        ...,
        description="A space-separated string of chess moves in standard algebraic notation (e.g., 'e4 e5 Nf3').",
        example="e4 e5 Nf3 Nc6",
    )
    variant: Optional[str] = "standard"
    initial_fen: Optional[str] = None


# GamePlayer (Relationship between game and players) Pydantic schema
class GamePlayerCreate(BaseModel):
    game_id: str
    player_id: str
    color: str
    rating_diff: Optional[int] = None
    rating: int

class GamePlayer(BaseModel):
    game_id: str
    player_id: str
    color: str
    rating_diff: Optional[int] = None
    rating: int

    class Config:
        orm_mode = True

class LastMoveTimeResponse(BaseModel):
    last_move_time: int # unix time in milliseconds

    class Config:
        orm_mode = True