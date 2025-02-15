from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from app.db.models import async_session as db_session_maker
from sqlalchemy import select
from app.db.models import ViralTweet, AccountMetric, AdaptationLog
from fastapi.responses import HTMLResponse
import datetime
from app.modules.content_generation import ContentGenerationModule

router = APIRouter()

class AggregatedAnalytics(BaseModel):
    viral_tweets: list
    metrics: list
    adaptation_logs: list

class ImageResponse(BaseModel):
    image_url: str

@router.get("/analytics", response_model=AggregatedAnalytics)
async def get_aggregated_analytics():
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(days=7)
    async with db_session_maker() as session:
        result_tweets = await session.execute(
            select(ViralTweet).where(ViralTweet.timestamp >= start, ViralTweet.timestamp <= now)
            .order_by(ViralTweet.retweet_ratio.desc())
        )
        tweets = result_tweets.scalars().all()
        tweets_data = [{"tweet_id": t.tweet_id, "text": t.text, "analysis": t.analysis, "retweet_ratio": t.retweet_ratio} for t in tweets]

        result_metrics = await session.execute(
            select(AccountMetric).where(AccountMetric.timestamp >= start, AccountMetric.timestamp <= now)
            .order_by(AccountMetric.timestamp.asc())
        )
        metrics = result_metrics.scalars().all()
        metrics_data = [{"followers_count": m.followers_count, "tweet_count": m.tweet_count, "engagement_rate": m.engagement_rate, "timestamp": m.timestamp.isoformat()} for m in metrics]

        result_logs = await session.execute(
            select(AdaptationLog).where(AdaptationLog.timestamp >= start, AdaptationLog.timestamp <= now)
            .order_by(AdaptationLog.timestamp.asc())
        )
        logs = result_logs.scalars().all()
        logs_data = [{"viral_tweet_id": l.viral_tweet_id, "analysis": l.analysis, "action_taken": l.action_taken, "result_metrics": l.result_metrics, "adaptation_parameters": l.adaptation_parameters, "timestamp": l.timestamp.isoformat()} for l in logs]
    return AggregatedAnalytics(viral_tweets=tweets_data, metrics=metrics_data, adaptation_logs=logs_data)

@router.get("/performance")
async def get_latest_performance():
    async with db_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(AccountMetric).order_by(AccountMetric.timestamp.desc()).limit(1)
        )
        metric = result.scalar_one_or_none()
        if metric:
            return {"followers_count": metric.followers_count, "tweet_count": metric.tweet_count, "engagement_rate": metric.engagement_rate, "timestamp": metric.timestamp.isoformat()}
        else:
            raise HTTPException(status_code=404, detail="No performance metrics available")

@router.post("/generate_tweet", summary="Generate a tweet based on prompt")
async def generate_tweet(prompt: str = Body(..., embed=True)):
    """
    Generates a tweet based on the provided prompt.
    """
    content_module = ContentGenerationModule()
    generated = await content_module.generate_content(prompt)
    return {"tweet": generated}

@router.post("/generate_image", summary="Generate an image based on input prompt")
async def generate_image(prompt: str = Body("", embed=True)):
    """
    Generates an image based on the provided prompt.
    Returns the base64-encoded image directly.
    """
    content_module = ContentGenerationModule()
    image_data = await content_module.generate_image(prompt)

    if not image_data or image_data == "No image URL returned.":
        raise HTTPException(status_code=500, detail="Image generation failed")

    return {"image": image_data}

@router.get("/recommendations")
async def get_recommendations():
    from app.modules.recommendation import RecommendationModule
    rec_module = RecommendationModule()
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(days=7)
    async with db_session_maker() as session:
        from sqlalchemy import select
        result_tweets = await session.execute(
            select(ViralTweet).where(ViralTweet.timestamp >= start, ViralTweet.timestamp <= now)
        )
        tweets = result_tweets.scalars().all()
        viral_tweets = [{"tweet_id": t.tweet_id, "retweet_ratio": t.retweet_ratio, "analysis": t.analysis, "text": t.text} for t in tweets]
    analytics_data = {"viral_tweets": viral_tweets}
    recommendation = await rec_module.generate_recommendation(analytics_data)
    return recommendation

@router.get("/adaptation_logs")
async def get_adaptation_logs():
    async with db_session_maker() as session:
        from sqlalchemy import select
        now = datetime.datetime.utcnow()
        start = now - datetime.timedelta(days=7)
        result_logs = await session.execute(
            select(AdaptationLog).where(AdaptationLog.timestamp >= start, AdaptationLog.timestamp <= now)
            .order_by(AdaptationLog.timestamp.asc())
        )
        logs = result_logs.scalars().all()
        logs_data = [{"viral_tweet_id": l.viral_tweet_id, "analysis": l.analysis, "action_taken": l.action_taken, "result_metrics": l.result_metrics, "adaptation_parameters": l.adaptation_parameters, "timestamp": l.timestamp.isoformat()} for l in logs]
    return {"adaptation_logs": logs_data}

@router.get("/most_viral_tweets", summary="Get the most viral tweets by retweet ratio")
async def get_most_viral_tweets(limit: int = Query(1, ge=1, le=10)):
    """
    Retrieves the most viral tweets from the database (based on retweet ratio).
    The number of tweets returned is specified by the 'limit' query parameter.
    """
    async with db_session_maker() as session:
        result = await session.execute(
            select(ViralTweet).order_by(ViralTweet.retweet_ratio.desc()).limit(limit)
        )
        tweets = result.scalars().all()
        
        if not tweets:
            raise HTTPException(status_code=404, detail="No viral tweets found")
        
        return [
            {
                "tweet_id": tweet.tweet_id,
                "text": tweet.text,
                "retweet_ratio": tweet.retweet_ratio,
                "analysis": tweet.analysis,
                "timestamp": tweet.timestamp.isoformat()
            }
            for tweet in tweets
        ]