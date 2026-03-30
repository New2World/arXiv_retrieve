import logging
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import AsyncSessionLocal
from app.services.fetch_orchestrator import run_fetch
from app.config import settings

logger = logging.getLogger(__name__)

# Global singleton scheduler (Forced UTC constraint matching Frontend UI offsets)
_scheduler = AsyncIOScheduler(timezone=datetime.timezone.utc)
_JOB_ID = "auto_fetch_job"

async def _scheduled_task():
    """Proxy task to execute fetch orchestration inside an isolated DB session context."""
    logger.info("Executing scheduled background fetch task...")
    try:
        async with AsyncSessionLocal() as session:
            await run_fetch(session)
        logger.info("Scheduled background fetch task completed successfully.")
    except Exception as e:
        logger.error(f"Error during scheduled background fetch: {e}")

def update_scheduler_job(current_settings=None):
    """
    Update or mount the APScheduler job based on current system settings.
    Safe to call during application REST configuration Hot-Reloads.
    """
    s = current_settings or settings
    
    if _scheduler.get_job(_JOB_ID):
        _scheduler.remove_job(_JOB_ID)
        
    if s.auto_fetch_enabled and s.auto_fetch_cron and str(s.auto_fetch_cron).strip().lower() != "none":
        try:
            # Parse our explicitly composed Unix/JS cron string dynamically neutralizing day indices.
            parts = s.auto_fetch_cron.split(" ")
            
            minute = parts[0] if len(parts) > 0 else "0"
            hour = parts[1] if len(parts) > 1 else "8"
            
            # 0=Sunday, 1=Monday... 6=Saturday mapping securely to APScheduler literals
            day_map = {"0": "sun", "1": "mon", "2": "tue", "3": "wed", "4": "thu", "5": "fri", "6": "sat", "*": "*"}
            dow_key = parts[4] if len(parts) > 4 else "*"
            dow_literal = day_map.get(dow_key, "*")

            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day_of_week=dow_literal,
                timezone=datetime.timezone.utc
            )
            
            _scheduler.add_job(
                _scheduled_task,
                trigger=trigger,
                id=_JOB_ID,
                replace_existing=True,
                misfire_grace_time=3600
            )
            logger.info(f"Scheduled auto_fetch mounted. Next mapping derived from Cron: {s.auto_fetch_cron}")
        except Exception as e:
            logger.error(f"Failed to mount APScheduler task using cron '{s.auto_fetch_cron}': {e}")
    else:
        logger.info("Auto fetch scheduler is manually disabled. Job detached.")

def init_scheduler():
    """Initializes and starts the background daemon mapping boot configurations."""
    if not _scheduler.running:
        _scheduler.start()
        logger.info("Background AsyncIOScheduler daemon instantiated & started.")
    update_scheduler_job()

def shutdown_scheduler():
    """Graceful kill targeting FastApi lifespan teardowns."""
    if _scheduler.running:
        _scheduler.shutdown()
        logger.info("Background AsyncIOScheduler explicitly halted.")
