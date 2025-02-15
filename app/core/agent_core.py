import asyncio
import logging
import datetime
import json
from app.config import Config
from app.db.models import Metric, AdaptationLog, ViralTweet, AdaptationSettings
from app.db.models import async_session as db_session_maker
from app.background_tasks import run_twitter_analytics_background, run_performance_tracking_background, run_weekly_adaptation
from fastapi import FastAPI, Depends
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from app.api.endpoints import router as api_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class AgentCore:
    """
    Core Engine:
      - Manages the overall cycle of the agent.
      - Aggregates all data accumulated during the adaptation period:
            * All viral tweets,
            * All recorded metrics,
            * Adaptation logs.
      - Runs an adaptation cycle via LangChain only once per defined interval (e.g., one week).
      - Saves a comprehensive adaptation log and updates AdaptationSettings.
      
      // Analyse sequence:
      // "Tweet → Analysis → Action → Result" и коррелируя их с метриками.
    """
    def __init__(self):
        self.config = Config()
        self.loop = asyncio.get_event_loop()
        self.cycle_count = 0
        self.last_adaptation_time = datetime.datetime.utcnow()

        # Initialize LangChain for adaptation feedback
        self.llm = ChatOpenAI(api_key=self.config.OPENAI_API_KEY, temperature=0.7, model_name="gpt-4o")
        adaptation_prompt_template = PromptTemplate(
            template=(
                "We have aggregated the following data from the past period:\n\n"
                "Viral Tweets:\n{viral_data}\n\n"
                "Metrics:\n{metrics_data}\n\n"
                "Action Logs:\n{logs_data}\n\n"
                "Based on these, suggest adjustments to our strategy in JSON format. "
                "Return a JSON with keys: viral_threshold (float), generation_style (string), posting_interval (integer in seconds)."
            ),
            input_variables=["viral_data", "metrics_data", "logs_data"]
        )
        self.adaptation_chain = LLMChain(llm=self.llm, prompt=adaptation_prompt_template)

    async def run_cycle(self):
        logger.info("Project initialization:")
        logger.info(f"Niche: {self.config.NICHE}, Style: {self.config.STYLE}, Rules: {self.config.RULES}")
        
        while True:
            self.cycle_count += 1
            logger.info(f"Cycle {self.cycle_count} started at {datetime.datetime.utcnow().isoformat()}.")

            current_time = datetime.datetime.utcnow()
            time_since_last = (current_time - self.last_adaptation_time).total_seconds()
            if time_since_last >= self.config.ADAPTATION_INTERVAL:
                logger.info("Adaptation period reached. Aggregating data for adaptation...")
                adaptation_data = await self.aggregate_adaptation_data(self.last_adaptation_time, current_time)
                if adaptation_data:
                    recommendation = await self.run_adaptation_cycle(adaptation_data)
                    logger.info("Adaptation recommendation: " + recommendation)
                    await self.save_adaptation_log(adaptation_data, recommendation)
                    await self.update_adaptation_settings(recommendation)
                else:
                    logger.info("No new data accumulated for adaptation.")
                self.last_adaptation_time = current_time

            await asyncio.sleep(86400) # everyday check

    async def aggregate_adaptation_data(self, start_time: datetime.datetime, end_time: datetime.datetime) -> dict:
        """
        Aggregates adaptation data from the database between start_time and end_time.
        Combines:
          - Top viral tweets (limited to MAX_VIRAL_TWEETS, sorted by retweet_ratio descending),
          - Metrics recorded during the period,
          - Adaptation logs (actions taken).
        Returns a dictionary with keys: viral_data, metrics_data, logs_data.
          
        // Пример: для более детального анализа можно расширить набор собираемых данных.
        """
        async with db_session_maker() as session:
            from sqlalchemy import select
            # Aggregate top viral tweets with limit from config
            result_tweets = await session.execute(
                select(ViralTweet)
                .where(ViralTweet.timestamp >= start_time, ViralTweet.timestamp <= end_time)
                .order_by(ViralTweet.retweet_ratio.desc())
                .limit(Config.MAX_VIRAL_TWEETS)
            )
            tweets = result_tweets.scalars().all()
            viral_texts = []
            if tweets:
                for tweet in tweets:
                    analysis_text = getattr(tweet, 'analysis', 'No analysis available')
                    viral_texts.append(f"Tweet: {tweet.text}\nAnalysis: {analysis_text}")
                viral_data = "\n\n".join(viral_texts)
            else:
                viral_data = "No viral tweets recorded."

            # Aggregate metrics
            result_metrics = await session.execute(
                select(Metric).where(Metric.timestamp >= start_time, Metric.timestamp <= end_time)
            )
            metrics = result_metrics.scalars().all()
            metrics_texts = []
            if metrics:
                for metric in metrics:
                    metrics_texts.append(f"Metric: {metric.name}, Value: {metric.value}, Time: {metric.timestamp.isoformat()}")
                metrics_data = "\n\n".join(metrics_texts)
            else:
                metrics_data = "No metrics recorded."

            # Aggregate adaptation logs (actions)
            result_logs = await session.execute(
                select(AdaptationLog).where(AdaptationLog.timestamp >= start_time, AdaptationLog.timestamp <= end_time)
            )
            logs = result_logs.scalars().all()
            logs_texts = []
            if logs:
                for log in logs:
                    logs_texts.append(
                        f"Action Log - Tweet ID: {log.viral_tweet_id}, Analysis: {log.analysis}, "
                        f"Action: {log.action_taken}, Result: {log.result_metrics}, Correction: {getattr(log, 'correction', '')}, Time: {log.timestamp.isoformat()}"
                    )
                logs_data = "\n\n".join(logs_texts)
            else:
                logs_data = "No adaptation logs recorded."

            aggregated_data = {
                "viral_data": viral_data,
                "metrics_data": metrics_data,
                "logs_data": logs_data
            }
            return aggregated_data

    async def run_adaptation_cycle(self, adaptation_data: dict) -> str:
        """
        Runs the adaptation cycle using LangChain based on aggregated adaptation data.
        """
        loop = asyncio.get_event_loop()
        recommendation = await loop.run_in_executor(
            None,
            self.adaptation_chain.run,
            adaptation_data
        )
        return recommendation.strip()

    async def save_adaptation_log(self, adaptation_data: dict, recommendation: str):
        """
        Saves a detailed adaptation log entry to the database.
        """
        async with db_session_maker() as session:
            log_entry = AdaptationLog(
                viral_tweet_id="Aggregated",  # Indicates aggregated data over the period
                analysis=json.dumps(adaptation_data),
                action_taken="Aggregated actions from business modules",  # Здесь можно расширить логику
                result_metrics="Aggregated results | Recommendation: " + recommendation,
                adaptation_parameters=recommendation,
                timestamp=datetime.datetime.utcnow()
            )
            session.add(log_entry)
            await session.commit()

    async def update_adaptation_settings(self, recommendation: str):
        """
        Parses the JSON recommendation and updates AdaptationSettings in the database.
        """
        try:
            settings_data = json.loads(recommendation)
        except json.JSONDecodeError:
            logger.error("Failed to parse adaptation recommendation JSON.")
            return
        
        async with db_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(select(AdaptationSettings))
            current_settings = result.scalar_one_or_none()
            if current_settings is None:
                current_settings = AdaptationSettings(
                    viral_threshold=settings_data.get("viral_threshold", 0.1),
                    generation_style=settings_data.get("generation_style", self.config.STYLE),
                    posting_interval=settings_data.get("posting_interval", 60),
                    default_correction=settings_data.get("correction", "")
                )
                session.add(current_settings)
            else:
                current_settings.viral_threshold = settings_data.get("viral_threshold", current_settings.viral_threshold)
                current_settings.generation_style = settings_data.get("generation_style", current_settings.generation_style)
                current_settings.posting_interval = settings_data.get("posting_interval", current_settings.posting_interval)
                if "correction" in settings_data:
                    current_settings.default_correction = settings_data["correction"]
            await session.commit()
            logger.info("Adaptation settings updated: " + str(settings_data))

    def start(self):
        try:
            self.loop.run_until_complete(self.run_cycle())
        except KeyboardInterrupt:
            logger.info("Agent stopped by user.")

    async def run_adaptation_cycle_once(self):
        current_time = datetime.datetime.utcnow()
        start_time = current_time - datetime.timedelta(seconds=self.config.ADAPTATION_INTERVAL)
        aggregated_data = await self.aggregate_adaptation_data(start_time, current_time)
        if aggregated_data:
            recommendation = await self.run_adaptation_cycle(aggregated_data)
            await self.save_adaptation_log(aggregated_data, recommendation)
            await self.update_adaptation_settings(recommendation)


if __name__ == "__main__":
    agent = AgentCore()
    agent.start()
