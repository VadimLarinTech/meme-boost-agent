import os
import asyncio
import tweepy
from sqlalchemy import select
from app.db.models import AccountMetric
from app.config import Config
from app.db.models import async_session as db_session_maker

class PerformanceTrackingModule:
    """
    Performance Tracking Module:
      - Retrieves Twitter account metrics via Twitter API.
      - Saves daily metrics to the database.
    """
    def __init__(self):
        self.client = tweepy.Client(bearer_token=Config.TWITTER_BEARER_TOKEN)
        self.account_id = Config.TWITTER_ACCOUNT_ID

    async def fetch_account_metrics(self) -> dict:
        try:
            response = await self.client.get_user(
                id=self.account_id, user_fields=["public_metrics"]
            )
            user = response.data
            metrics = user.public_metrics
            account_data = {
                "followers_count": metrics.get("followers_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
                "engagement_rate": 0.0  
            }
            return account_data
        except tweepy.TweepyException as e:
            return {}

    async def collect_daily_metrics(self):
        """
        Fetches account metrics and saves them in the database.
        This task should be scheduled to run once per day.
        """
        data = await self.fetch_account_metrics()
        if data:
            async with db_session_maker() as session:
                new_metric = AccountMetric(
                    account_id=self.account_id,
                    followers_count=data.get("followers_count", 0),
                    tweet_count=data.get("tweet_count", 0),
                    engagement_rate=data.get("engagement_rate", 0.0)
                )
                session.add(new_metric)
                await session.commit()

    async def get_latest_metrics(self) -> dict:
        async with db_session_maker() as session:
            result = await session.execute(
                select(AccountMetric).order_by(AccountMetric.timestamp.desc()).limit(1)
            )
            metric = result.scalar_one_or_none()
            if metric:
                return {
                    "followers_count": metric.followers_count,
                    "tweet_count": metric.tweet_count,
                    "engagement_rate": metric.engagement_rate,
                    "timestamp": metric.timestamp.isoformat()
                }
            return {}
