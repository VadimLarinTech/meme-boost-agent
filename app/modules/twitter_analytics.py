import asyncio
import datetime
import tweepy
from sqlalchemy import select
from app.db.models import ViralTweet, AdaptationSettings
from app.config import Config
from app.db.models import async_session as db_session_maker
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TwitterAnalyticsModule:
    """
    Twitter Analytics Module:
      - Uses tweepy.AsyncClient to perform real Twitter API calls.
      - Retrieves tweets based on a static query from Config.
      - Determines viral tweets based on public metrics and an adaptive threshold.
      - Uses LLM via LangChain to analyze tweet text and extract viral factors.
      - Saves both the tweet and its analysis into the database.
      
      // При агрегировании будут выбраны топ MAX_VIRAL_TWEETS записей.
    """
    def __init__(self):
        # If TWITTER_BEARER_TOKENS is set, split by comma; otherwise, use single token
        tokens = Config.TWITTER_BEARER_TOKEN
        if tokens:
            self.bearer_tokens = [token.strip() for token in tokens.split(",")]
        else:
            self.bearer_tokens = [Config.TWITTER_BEARER_TOKEN]
        self.current_key_index = 0
        self.client = tweepy.Client(bearer_token=self.bearer_tokens[self.current_key_index])
        self.query_list = [q.strip() for q in Config.TWITTER_QUERY.split(",") if q.strip()]
        self.viral_threshold = Config.VIRAL_THRESHOLD
        self.llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, temperature=0.7, model_name="gpt-4o")
        analysis_prompt_template = PromptTemplate(
            template=(
                "Analyze the following tweet and list the factors that contributed to its virality.\n"
                "Tweet text: {tweet_text}\n"
                "Provide a concise analysis."
            ),
            input_variables=["tweet_text"]
        )
        self.analysis_chain = LLMChain(llm=self.llm, prompt=analysis_prompt_template)

    async def update_parameters(self):
        async with db_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(select(AdaptationSettings))
            settings = result.scalar_one_or_none()
            if settings:
                self.viral_threshold = settings.viral_threshold

    async def fetch_and_analyze(self) -> dict:
        await self.update_parameters()  # update threshold before processing
        max_retries = 5
        delay = 60
        loop = asyncio.get_event_loop()
        accumulated_viral = {}
        tweets = []

        for query in self.query_list:
            for attempt in range(max_retries):
                try:
                    response = await loop.run_in_executor(
                        None,
                        lambda q=query: self.client.search_recent_tweets(
                            query=q,
                            max_results=10,
                            tweet_fields=["public_metrics", "lang", "author_id"],
                            expansions=["author_id"],
                            user_fields=["public_metrics"]
                        )
                    )
                    tweets = response.data

                    if not tweets:
                        return {}

                    users = {}
                    if response.includes and 'users' in response.includes:
                        for user in response.includes['users']:
                            users[user.id] = user

                    viral_tweets = []
                    for tweet in tweets:
                        tweet_text = tweet.text
                        # Exclude duplicates by tweet text
                        if any(existing.get("text") == tweet_text for existing in accumulated_viral.values()):
                            continue

                        tweet_metrics = tweet.public_metrics
                        author = users.get(tweet.author_id)
                        if not author:
                            continue

                        user_metrics = author.public_metrics
                        followers_count = user_metrics.get('followers_count', 0)
                        if followers_count < 5:
                            continue

                        retweet_ratio = tweet_metrics.get('retweet_count', 0) / followers_count
                        like_ratio = tweet_metrics.get('like_count', 0) / followers_count

                        if retweet_ratio >= self.viral_threshold or like_ratio >= self.viral_threshold:
                            tweet_id = str(tweet.id)
                            tweet_data = {
                                'tweet_id': str(tweet.id),
                                'text': tweet.text,
                                'retweet_count': tweet_metrics.get('retweet_count', 0),
                                'like_count': tweet_metrics.get('like_count', 0),
                                'followers_count': followers_count,
                                'retweet_ratio': retweet_ratio,
                                'like_ratio': like_ratio
                            }
                            analysis = await self.analyze_viral_tweet(tweet.text)
                            tweet_data["analysis"] = analysis
                            accumulated_viral[tweet_id] = tweet_data
                            await self.save_viral_tweet(tweet_data)

                    if len(accumulated_viral) >= 5:
                        print(f"Accumulated {len(accumulated_viral)} viral tweets from query '{query}'.")
                        break

                    await asyncio.sleep(delay)
                    delay *= 2
                except tweepy.TweepyException as e:
                    if '429' in str(e):
                        print("Rate limit encountered. Rotating token...")
                        # Rotate bearer token on rate limit
                        self.current_key_index = (self.current_key_index + 1) % len(self.bearer_tokens)
                        self.client = tweepy.Client(bearer_token=self.bearer_tokens[self.current_key_index])
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        continue
            if len(accumulated_viral) >= 5:
                    break

        analytics_data = {
            'query': ", ".join(self.query_list),
            'tweets_count': len(tweets) if tweets else 0,
            'viral_tweets': list(accumulated_viral.values()),
            'sentiment': 'positive'
        }
        return analytics_data

    async def analyze_viral_tweet(self, tweet_text: str) -> str:
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(
            None,
            self.analysis_chain.run,
            {"tweet_text": tweet_text}
        )
        return analysis.strip()

    async def save_viral_tweet(self, tweet_data: dict):
        async with db_session_maker() as session:
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
                    like_ratio=tweet_data['like_ratio'],
                    analysis=tweet_data.get("analysis")
                )
                session.add(new_tweet)
                await session.commit()
