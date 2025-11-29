import logging
import requests
import chess
import chess.engine
import chess.pgn
import io
from analysis.plugins.largest_swing import LargestSwingPlugin
from utils.config import settings
from celery_app import app, redis_client

# Register plugins
PLUGINS = [
    LargestSwingPlugin()
]

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Configures periodic tasks (Celery Beat) for analysis.
    """
    # Run analysis enqueuer every 60 seconds
    sender.add_periodic_task(60.0, enqueue_analysis_tasks.s(), name='analysis-enqueuer-every-60-seconds')
    
    # Trigger immediately on startup
    enqueue_analysis_tasks.delay()

@app.task(queue='analysis_queue')
def analyze_game(game_id: str):
    """
    Performs analysis on a game using Stockfish and registered plugins.
    """
    logging.info(f"Starting analysis for game {game_id}")
    
    # 0. Fetch existing metrics to check per-plugin status later
    existing_metrics = None
    try:
        url = f"http://{settings.fastapi_route}/games/{game_id}/metrics"
        response = requests.get(url)
        if response.status_code == 200:
            existing_metrics = response.json()
    except Exception as e:
        logging.warning(f"Failed to check existing metrics for {game_id}: {e}")

    # 1. Fetch PGN from API
    try:
        url = f"http://{settings.fastapi_route}/games/{game_id}/pgn"
        response = requests.get(url)
        response.raise_for_status()
        pgn_text = response.json().get("pgn")
        
        if not pgn_text:
            logging.warning(f"No PGN found for game {game_id}")
            # Clear pending status if we can't analyze
            redis_client.delete(f"analysis_pending:{game_id}")
            return

        # 2. Parse PGN
        pgn = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)
        
        if not game:
            logging.error(f"Failed to parse PGN for game {game_id}")
            return

        # 3. Initialize Engine
        # Ensure stockfish is in the PATH (installed via apt-get)
        engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        
        results = {}
        
        try:
            # 4. Run Plugins
            for plugin in PLUGINS:
                # Check if this plugin already ran
                if existing_metrics and existing_metrics.get("metrics") and plugin.name in existing_metrics["metrics"]:
                    logging.info(f"Skipping plugin {plugin.name} for game {game_id}: Already exists.")
                    continue
                
                logging.info(f"Running plugin {plugin.name} for game {game_id}")
                plugin_result = plugin.analyze(game, engine)
                results[plugin.name] = plugin_result
                
        finally:
            engine.quit()
            
        # 5. Save Results
        if results:
            url = f"http://{settings.fastapi_route}/games/{game_id}/metrics"
            response = requests.post(url, json=results)
            response.raise_for_status()
            logging.info(f"Saved analysis metrics for game {game_id}")
        else:
            logging.info(f"No new analysis results to save for game {game_id}")
            
        # Clear pending status
        redis_client.delete(f"analysis_pending:{game_id}")
            
    except Exception as e:
        logging.error(f"Error analyzing game {game_id}: {e}")
        # Retry logic?
        # self.retry(exc=e, countdown=60, max_retries=3)

@app.task(queue='analysis_scheduling_queue')
def enqueue_analysis_tasks():
    """
    Periodic task to find games needing analysis and enqueue them.
    """
    try:
        # Get list of active plugin names
        plugin_names = [p.name for p in PLUGINS]
        
        # Ask API for games needing analysis (fetch more to skip pending ones)
        url = f"http://{settings.fastapi_route}/games/analysis/queue"
        # Request 1000 candidates
        response = requests.post(url, json=plugin_names, params={"limit": 1000}) 
        response.raise_for_status()
        
        game_ids = response.json()
        
        enqueued_count = 0
        target_enqueue_count = 100 # We want to add ~100 tasks per run
        
        for game_id in game_ids:
            if enqueued_count >= target_enqueue_count:
                break
                
            # Deduplication: Check if game is already pending analysis
            # Key expires in 1 hour (3600s) to handle backlogs
            redis_key = f"analysis_pending:{game_id}"
            if redis_client.exists(redis_key):
                continue
                
            # Set key to mark as pending
            redis_client.set(redis_key, "1", ex=3600)
            
            analyze_game.delay(game_id)
            enqueued_count += 1
            
        if enqueued_count > 0:
            logging.info(f"Enqueued {enqueued_count} games for analysis")
            
    except Exception as e:
        logging.error(f"Error enqueuing analysis tasks: {e}")
