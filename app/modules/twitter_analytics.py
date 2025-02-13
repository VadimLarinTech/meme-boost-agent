import asyncio
import tweepy
from app.db.models import ViralTweet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class TwitterAnalyticsModule:
    """
    Модуль аналитики Twitter:
      - Использует tweepy.AsyncClient для вызовов к Twitter API.
      - Загружает данные по заданному запросу, анализирует их для определения виральных твитов,
        и сохраняет наиболее виральные твиты в базу данных.
    """
    def __init__(self, config: dict, db_session_maker):
        self.client = tweepy.AsyncClient(bearer_token=config['TWITTER_BEARER_TOKEN'])
        self.query = config.get('TWITTER_QUERY', 'crypto')
        self.db_session_maker = db_session_maker

    async def fetch_and_analyze(self) -> dict:
        max_retries = 5
        delay = 60  # начальная задержка в секундах при превышении лимита запросов

        for attempt in range(max_retries):
            try:
                response = await self.client.search_recent_tweets(
                    query=self.query,
                    max_results=10,
                    tweet_fields=["public_metrics", "lang", "author_id"],
                    expansions=["author_id"],
                    user_fields=["public_metrics"]
                )
                tweets = response.data

                if not tweets:
                    print("Нет найденных твитов.")
                    return {}

                users = {}
                if response.includes and 'users' in response.includes:
                    for user in response.includes['users']:
                        users[user.id] = user

                viral_tweets = []
                for tweet in tweets:
                    tweet_metrics = tweet.public_metrics
                    author = users.get(tweet.author_id)
                    if not author:
                        continue
                    user_metrics = author.public_metrics
                    followers_count = user_metrics.get('followers_count', 0)
                    if followers_count == 0:
                        continue

                    retweet_ratio = tweet_metrics.get('retweet_count', 0) / followers_count
                    like_ratio = tweet_metrics.get('like_count', 0) / followers_count

                    # Определяем "виральный" твит: соотношение ретвитов или лайков ≥ 10%
                    if retweet_ratio >= 0.1 or like_ratio >= 0.1:
                        tweet_data = {
                            'tweet_id': str(tweet.id),
                            'text': tweet.text,
                            'retweet_count': tweet_metrics.get('retweet_count', 0),
                            'like_count': tweet_metrics.get('like_count', 0),
                            'followers_count': followers_count,
                            'retweet_ratio': retweet_ratio,
                            'like_ratio': like_ratio
                        }
                        viral_tweets.append(tweet_data)
                        await self.save_viral_tweet(tweet_data)

                analytics_data = {
                    'query': self.query,
                    'tweets_count': len(tweets),
                    'viral_tweets': viral_tweets,
                    # Здесь можно добавить реальный анализ sentiment
                    'sentiment': 'positive'  
                }
                return analytics_data

            except tweepy.TweepyException as e:
                if '429' in str(e):
                    print(f"Лимит запросов превышен. Ожидание {delay} секунд перед повторной попыткой...")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    print("Ошибка при подключении к Twitter API:", e)
                    return {}
        return {}

    async def save_viral_tweet(self, tweet_data: dict):
        """
        Сохраняет виральный твит в базу данных, если его ещё нет.
        """
        async with self.db_session_maker() as session:
            # Проверяем, существует ли уже твит с таким tweet_id
            result = await session.execute(
                select(ViralTweet).where(ViralTweet.tweet_id == tweet_data['tweet_id'])
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                new_tweet = ViralTweet(
                    tweet_id=tweet_data['tweet_id'],
                    text=tweet_data['text'],
                    retweet_count=tweet_data['retweet_count'],
                    like_count=tweet_data['like_count'],
                    followers_count=tweet_data['followers_count'],
                    retweet_ratio=tweet_data['retweet_ratio'],
                    like_ratio=tweet_data['like_ratio']
                )
                session.add(new_tweet)
                await session.commit()
