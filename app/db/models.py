# app/db/models.py
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import Config

Base = declarative_base()

engine = create_async_engine(Config.DATABASE_URL, echo=True)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ViralTweet(Base):
    __tablename__ = "viral_tweets"
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, unique=True, index=True, nullable=False)
    text = Column(String)
    retweet_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)
    retweet_ratio = Column(Float, default=0.0)
    like_ratio = Column(Float, default=0.0)
    analysis = Column(String)  # LLM analysis of the tweet
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AccountMetric(Base):
    __tablename__ = "account_metrics"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, unique=True, index=True, nullable=False)
    followers_count = Column(Integer, default=0)
    tweet_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AdaptationLog(Base):
    __tablename__ = "adaptation_logs"
    id = Column(Integer, primary_key=True, index=True)
    viral_tweet_id = Column(String, nullable=True)  # Tweet ID if applicable
    analysis = Column(String, nullable=True)        # LLM analysis of the tweet
    action_taken = Column(String, nullable=True)      # Action performed (e.g., retweet, new tweet generation)
    result_metrics = Column(String, nullable=True)    # Outcome metrics (e.g., engagement improvement)
    adaptation_parameters = Column(String, nullable=True)  # JSON string with parameters (e.g., thresholds, style, posting interval)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AdaptationSettings(Base):
    __tablename__ = "adaptation_settings"
    id = Column(Integer, primary_key=True, index=True)
    viral_threshold = Column(Float, default=0.1)      # Threshold for viral tweet selection
    generation_style = Column(String, default="Humorous")  # Style used for content generation
    posting_interval = Column(Integer, default=60)    # Posting interval in seconds
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    correction = Column(String, nullable=True)