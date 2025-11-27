import logging
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from shared.models import GameFeature
from shared.config import settings

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Handles writing analysis results to the PostgreSQL database.
    """
    def __init__(self, db_url: str = None):
        if db_url is None:
            # Construct DB URL from settings if not provided
            # Assuming settings has these fields based on .env
            # We might need to adjust this based on actual settings object
            user = settings.postgres_user
            password = settings.postgres_password
            db = settings.postgres_db
            # Use 'postgres' service name if running in docker network, or localhost if local
            # But this code runs in Celery which is in Docker.
            # Let's rely on the passed db_url or a default constructed one.
            # For now, let's assume we can get it from os.environ or settings.
            # The settings object in utils/config.py likely has it.
            pass
        
        # We will use the sqlalchemy engine. 
        # Note: We need to be careful about connection pooling in Celery.
        # It's often better to create a fresh engine/session per task or use a pool.
        self.engine = create_engine(settings.database_url)
        self.Session = sessionmaker(bind=self.engine)

    def save_features(self, game_id: str, features: List[Dict[str, Any]]):
        """
        Saves a list of features for a given game.
        Uses 'upsert' logic (ON CONFLICT DO UPDATE).
        """
        if not features:
            return

        session = self.Session()
        try:
            # Prepare data for bulk insert
            values = []
            for f in features:
                values.append({
                    "game_id": game_id,
                    "feature_name": f["feature_name"],
                    "feature_value": str(f["feature_value"]), # Ensure string storage
                    "feature_type": f["feature_type"]
                })

            stmt = insert(GameFeature).values(values)
            
            # Upsert: Update value and type if feature already exists for this game
            stmt = stmt.on_conflict_do_update(
                index_elements=['game_id', 'feature_name'],
                set_={
                    "feature_value": stmt.excluded.feature_value,
                    "feature_type": stmt.excluded.feature_type
                }
            )

            session.execute(stmt)
            session.commit()
            logger.info(f"Saved {len(features)} features for game {game_id}")

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save features for game {game_id}: {e}")
            raise
        finally:
            session.close()
