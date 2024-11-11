from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, TIMESTAMP, PrimaryKeyConstraint, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    __table_args__ = {'schema': 'chess'}
    
    id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    lichess_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    flair = Column(String(255))

class Game(Base):
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
    __tablename__ = 'game_moves'
    __table_args__ = {'schema': 'chess'}
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String(255), ForeignKey('chess.games.game_id', ondelete='CASCADE'), nullable=False)
    move_number = Column(Integer, nullable=False)
    move = Column(Text, nullable=False)

class GamePlayer(Base):
    __tablename__ = 'game_players'
    __table_args__ = (
        PrimaryKeyConstraint('game_id', 'player_id'),
        {'schema': 'chess'},
    )
    
    game_id = Column(String(255), ForeignKey('chess.games.game_id', ondelete='CASCADE'), nullable=False)
    player_id = Column(Integer, ForeignKey('chess.players.id', ondelete='CASCADE'), nullable=False)
    color = Column(String(5), nullable=False)
    rating_diff = Column(Integer)
    rating = Column(Integer)
