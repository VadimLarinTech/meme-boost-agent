import datetime
from app.config import Config
from app.db.models import AdaptationSettings
from app.db.models import async_session as db_session_maker
from sqlalchemy import select

class RecommendationModule:
    """
    Recommendation Module:
      - Analyzes Twitter analytics data (including viral tweets and their analysis).
      - Provides recommendations such as which tweet to retweet, who to follow, optimal posting time, and tweet topic.
      - Uses adaptation settings to update the posting interval.
    """
    def __init__(self):
        self.posting_interval = 60  # default; updated via adaptation settings

    async def update_parameters(self):
        async with db_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(select(AdaptationSettings))
            settings = result.scalar_one_or_none()
            if settings:
                self.posting_interval = settings.posting_interval

    async def generate_recommendation(self, analytics_data: dict) -> dict:
        await self.update_parameters()
        recommendation = {}
        viral_tweets = analytics_data.get("viral_tweets", [])
        if viral_tweets:
            best_tweet = max(viral_tweets, key=lambda t: t['retweet_ratio'])
            recommendation["retweet"] = {
                "tweet_id": best_tweet['tweet_id'],
                "text": best_tweet['text'],
                "analysis": best_tweet.get("analysis", "")
            }
            recommendation["follow"] = f"Follow the author of tweet {best_tweet['tweet_id']}"
        else:
            recommendation["retweet"] = None
            recommendation["follow"] = None

        optimal_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.posting_interval)
        recommendation["optimal_tweet_time"] = optimal_time.isoformat() + "Z"
        recommendation["tweet_topic"] = "Discuss the latest trends in crypto and meme coins."
        return recommendation
