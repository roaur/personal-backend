"""
Pydantic Schemas for API Data Validation.

This module defines the data contracts (schemas) for the API using Pydantic.
These schemas are used for:
1. Request Body Validation (e.g., GameCreate).
2. Response Serialization (e.g., Game).

Naming Convention:
- *Create: Used for POST requests (input).
- [ModelName]: Used for responses (output), usually includes ORM mode.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# =============================================================================
# Game Schemas
# =============================================================================

class Clock(BaseModel):
    """Nested schema for clock settings."""
    initial: int
    increment: int
    total_time: int

class GameCreate(BaseModel):
    """
    Schema for creating a new game.
    Matches the structure of the Lichess API response.
    """
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
    clock: Clock  # Nested object in input

class Game(BaseModel):
    """
    Schema for reading a game (Response).
    Flattens the clock data for easier consumption.
    """
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
    # Flattened clock fields
    clock_initial: int
    clock_increment: int
    clock_total_time: int

    class Config:
        orm_mode = True

# =============================================================================
# Player Schemas
# =============================================================================

class PlayerCreate(BaseModel):
    """Schema for creating/updating a player."""
    player_id: str
    name: str
    flair: Optional[str] = None
    last_fetched_at: Optional[datetime] = None
    depth: Optional[int] = None

class Player(BaseModel):
    """Schema for reading a player."""
    player_id: str
    name: str
    flair: Optional[str] = None
    last_fetched_at: Optional[datetime] = None
    depth: Optional[int] = None

    class Config:
        orm_mode = True

# =============================================================================
# Move Schemas
# =============================================================================

class GameMove(BaseModel):
    """Schema for a single move record."""
    id: int
    game_id: str
    move_number: int
    move: str

    class Config:
        orm_mode = True

class MovesInput(BaseModel):
    """
    Schema for the 'add moves' endpoint input.
    Accepts a raw space-separated string of moves.
    """
    moves: str = Field(
        ...,
        description="A space-separated string of chess moves in standard algebraic notation (e.g., 'e4 e5 Nf3').",
        example="e4 e5 Nf3 Nc6",
    )
    variant: Optional[str] = "standard"
    initial_fen: Optional[str] = None


# =============================================================================
# Game-Player Relationship Schemas
# =============================================================================

class GamePlayerCreate(BaseModel):
    """Schema for linking a player to a game."""
    game_id: str
    player_id: str
    color: str
    rating_diff: Optional[int] = None
    rating: int

class GamePlayer(BaseModel):
    """Schema for reading a game-player link."""
    game_id: str
    player_id: str
    color: str
    rating_diff: Optional[int] = None
    rating: int

    class Config:
        orm_mode = True

class LastMoveTimeResponse(BaseModel):
    """Schema for the last move time response."""
    last_move_time: int # unix time in milliseconds

    class Config:
        orm_mode = True

class PlayerProcessResponse(Player):
    """Schema for a player with their last move time."""
    last_move_time: int # unix time in milliseconds

    class Config:
        orm_mode = True

# =============================================================================
# Analysis Schemas
# =============================================================================

class GameMetricsCreate(BaseModel):
    """Schema for creating/updating game metrics."""
    game_id: str
    metrics: dict

class GameMetrics(BaseModel):
    """Schema for reading game metrics."""
    id: int
    game_id: str
    metrics: dict

    class Config:
        orm_mode = True