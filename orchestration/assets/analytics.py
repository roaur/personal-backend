from dagster import asset, Output, AssetContext
from common.analytics.registry import discover_analytics
from common.analytics.base import BaseAnalytic
from common.database import AsyncSessionLocal
from common.models import Game, AnalysisStatus, AnalyticsType, GameMetrics
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert
import chess.pgn
import io
import asyncio

# Discover plugins
analytics_plugins = discover_analytics()

def make_analytic_asset(plugin_class: type[BaseAnalytic]):
    plugin = plugin_class()
    asset_name = f"analytic_{plugin.name}"
    
    @asset(name=asset_name, group_name="analytics")
    async def analytic_asset(context: AssetContext):
        async with AsyncSessionLocal() as session:
            # 1. Ensure AnalyticType exists
            stmt = insert(AnalyticsType).values(
                name=plugin.name,
                version=plugin.version
            ).on_conflict_do_update(
                index_elements=['name'],
                set_=dict(version=plugin.version)
            ).returning(AnalyticsType.id)
            
            result = await session.execute(stmt)
            analytic_id = result.scalar_one()
            
            # 2. Find games needing analysis (Left Join)
            # SELECT g.game_id, g.pgn FROM games g 
            # LEFT JOIN analysis_status s ON g.game_id = s.game_id AND s.analytic_id = :id 
            # WHERE s.id IS NULL
            # LIMIT 100 (Batch size)
            
            subq = select(AnalysisStatus.id).where(
                and_(
                    AnalysisStatus.game_id == Game.game_id,
                    AnalysisStatus.analytic_id == analytic_id
                )
            ).exists()
            
            query = select(Game).where(~subq).limit(100)
            result = await session.execute(query)
            games_to_analyze = result.scalars().all()
            
            context.log.info(f"Found {len(games_to_analyze)} games to analyze for {plugin.name}")
            
            for game_row in games_to_analyze:
                try:
                    # Parse PGN
                    pgn = io.StringIO(game_row.pgn)
                    game = chess.pgn.read_game(pgn)
                    
                    # Analyze
                    metrics = plugin.analyze(game)
                    
                    # Update Metrics
                    # We need to merge metrics. This is a bit complex with JSONB in async SA.
                    # For now, let's just fetch, update, save.
                    # Ideally we use jsonb_set or similar but python-side merge is easier for MVP.
                    
                    # Upsert GameMetrics
                    # Check if exists
                    gm_query = select(GameMetrics).where(GameMetrics.game_id == game_row.game_id)
                    gm_result = await session.execute(gm_query)
                    gm = gm_result.scalar_one_or_none()
                    
                    if not gm:
                        gm = GameMetrics(game_id=game_row.game_id, metrics={})
                        session.add(gm)
                    
                    # Update dict
                    current_metrics = dict(gm.metrics) if gm.metrics else {}
                    current_metrics.update({plugin.name: metrics})
                    gm.metrics = current_metrics
                    
                    # Mark Status
                    status = AnalysisStatus(
                        game_id=game_row.game_id,
                        analytic_id=analytic_id,
                        status="completed",
                        updated_at=game_row.last_move_at # or now()
                    )
                    session.add(status)
                    
                except Exception as e:
                    context.log.error(f"Failed to analyze game {game_row.game_id}: {e}")
                    # Mark as failed
                    status = AnalysisStatus(
                        game_id=game_row.game_id,
                        analytic_id=analytic_id,
                        status="failed",
                        updated_at=game_row.last_move_at
                    )
                    session.add(status)
            
            await session.commit()
            
        return Output(len(games_to_analyze), metadata={"count": len(games_to_analyze)})

    return analytic_asset

# Create assets list
analytic_assets = [make_analytic_asset(plugin) for plugin in analytics_plugins]
