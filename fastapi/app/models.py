"""
SQLAlchemy Models for the Chess Data Application.

This module defines the database schema using SQLAlchemy ORM.
It maps Python classes to PostgreSQL tables in the 'chess' schema.

Key Models:
- Player: Stores player information (ID, name, fetch status).
- Game: Stores game metadata (ID, PGN, status, time control).
- GameMove: Stores individual moves for a game (one row per move).
- GamePlayer: Link table between Games and Players (many-to-many), storing color and rating.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, TIMESTAMP, PrimaryKeyConstraint, Numeric, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):
    """
    Represents a Chess Player.
    
    Attributes:
        player_id (Text): Unique Lichess username (lowercase). Primary Key.
        name (String): Display name of the player.
        flair (String): Optional flair/icon associated with the player.
        last_fetched_at (TIMESTAMP): When this player's games were last fetched.
        depth (Integer): Graph traversal depth (0 = main user, 1 = opponent, etc.).
    """
    __tablename__ = 'players'
    __table_args__ = {'schema': 'chess'}
    
    player_id = Column(Text, unique=True, nullable=False, primary_key=True)
    name = Column(String(255), nullable=False)
    flair = Column(String(255))
    last_fetched_at = Column(TIMESTAMP(timezone=True))
    depth = Column(Integer)

class Game(Base):
    """
    Represents a Chess Game.
    
    Attributes:
        game_id (String): Unique Lichess game ID. Primary Key.
        rated (Boolean): Whether the game was rated.
        variant (String): Game variant (standard, blitz, etc.).
        speed (String): Game speed category (bullet, blitz, rapid, classical).
        perf (String): Performance rating category.
        created_at (TIMESTAMP): Game start time.
        last_move_at (TIMESTAMP): Game end time (or last move time).
        status (String): Game status (mate, resign, draw, etc.).
        winner (String): 'white', 'black', or None (draw).
        pgn (Text): Full PGN (Portable Game Notation) string.
        clock_initial (Integer): Initial clock time in seconds.
        clock_increment (Integer): Clock increment in seconds.
        clock_total_time (Integer): Total estimated game time.
    """
    __tablename__ = 'games'
    __table_args__ = {'schema': 'chess'}
    
    game_id = Column(String(255), primary_key=True)
    rated = Column(Boolean, nullable=False)
    variant = Column(String(50), nullable=False)
    speed = Column(String(50), nullable=False)
    perf = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    last_move_at = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String(50), nullable=False)
    source = Column(String(50))
    winner = Column(String(50))
    pgn = Column(Text)
    clock_initial = Column(Integer)
    clock_increment = Column(Integer)
    clock_total_time = Column(Integer)

class GameMove(Base):
    """
    Represents a single move in a game.
    
    Attributes:
        id (Integer): Auto-incrementing primary key.
        game_id (String): Foreign Key to games.game_id.
        move_number (Integer): The move number (1, 2, 3...).
        move (Text): The move in SAN (Standard Algebraic Notation), e.g., "e4".
    """
    __tablename__ = 'game_moves'
    __table_args__ = {'schema': 'chess'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(255), ForeignKey('chess.games.game_id', ondelete='CASCADE'), nullable=False)
    move_number = Column(Integer, nullable=False)
    move = Column(Text, nullable=False)

class GamePlayer(Base):
    """
    Association table linking Games and Players.
    
    Attributes:
        game_id (String): Foreign Key to games.game_id.
        player_id (Text): Foreign Key to players.player_id.
        color (Text): 'white' or 'black'.
        rating (Integer): Player's rating in this game.
        rating_diff (Integer): Rating change after this game.
    """
    __tablename__ = 'game_players'
    __table_args__ = (
        PrimaryKeyConstraint('game_id', 'player_id'),
        {'schema': 'chess'},
    )
    
    game_id = Column(String(255), ForeignKey('chess.games.game_id', ondelete='CASCADE'), nullable=False)
    player_id = Column(Text, ForeignKey('chess.players.player_id', ondelete='CASCADE'), nullable=False)
    color = Column(Text, nullable=False)
    rating_diff = Column(Integer)
    rating = Column(Integer)

class GameMetrics(Base):
    """
    Stores metric values for a specific game in a JSONB column.
    """
    __tablename__ = 'game_metrics'
    __table_args__ = (
        Index('ix_game_metrics_metrics', 'metrics', postgresql_using='gin'),
        {'schema': 'chess'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Text, ForeignKey('chess.games.game_id', ondelete='CASCADE'), unique=True, nullable=False)
    metrics = Column(JSONB, nullable=False, default={})