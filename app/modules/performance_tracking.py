import asyncio
import tweepy
from sqlalchemy import select
from app.db.models import AccountMetric
from sqlalchemy.ext.asyncio import AsyncSession

class PerformanceTrackingModule:
    """
    Модуль отслеживания эффективности:
      - Получает метрики активности Twitter аккаунта (например, число подписчиков, твитов).
      - Сохраняет полученные данные в базу.
      - Предоставляет последние метрики для анализа эффективности.
    """
    def __init__(self, config: dict, db_session_maker):
        self.config = config
        self.db_session_maker = db_session_maker
        # Для получения метрик аккаунта используем Tweepy (OAuth2)
        self.client = tweepy.AsyncClient(bearer_token=config['TWITTER_BEARER_TOKEN'])
        self.account_id = config.get("TWITTER_ACCOUNT_ID")  # ID отслеживаемого аккаунта

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
                # engagement_rate можно рассчитать дополнительно, если доступны нужные данные
                "engagement_rate": 0.0  
            }
            return account_data
        except tweepy.TweepyException as e:
            print("Ошибка при получении метрик аккаунта:", e)
            return {}

    async def store_account_metrics(self, metrics: dict):
        async with self.db_session_maker() as session:
            new_metric = AccountMetric(
                account_id=self.account_id,
                followers_count=metrics.get("followers_count", 0),
                tweet_count=metrics.get("tweet_count", 0),
                engagement_rate=metrics.get("engagement_rate", 0.0)
            )
            session.add(new_metric)
            await session.commit()

    async def get_latest_metrics(self) -> dict:
        async with self.db_session_maker() as session:
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
