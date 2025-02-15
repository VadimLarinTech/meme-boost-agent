import asyncio
import logging
from app.modules.twitter_analytics import TwitterAnalyticsModule
from app.modules.performance_tracking import PerformanceTrackingModule
from app.config import Config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def run_twitter_analytics_background():
    analytics_module = TwitterAnalyticsModule()
    while True:
        try:
            await analytics_module.fetch_and_analyze()
        except Exception as e:
            logger.error(f"Error in Twitter analytics background task: {e}")
        # Run every 5 minutes
        await asyncio.sleep(300)

async def run_performance_tracking_background():
    performance_module = PerformanceTrackingModule()
    while True:
        try:
            await performance_module.collect_daily_metrics()
        except Exception as e:
            logger.error(f"Error in performance tracking background task: {e}")
        # Run every 24 hours (86400 seconds)
        await asyncio.sleep(Config.PERFORMANCE_TRACKING_INTERVAL)

async def run_weekly_adaptation():
    from app.core.agent_core import AgentCore
    agent = AgentCore()
    while True:
        try:
            await asyncio.sleep(Config.ADAPTATION_INTERVAL)
            await agent.run_adaptation_cycle_once()
        except Exception as e:
            logger.error(f"Error in weekly adaptation task: {e}")
