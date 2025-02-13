# app/db/models.py
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ViralTweet(Base):
    __tablename__ = "viral_tweets"
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, unique=True, index=True)
    text = Column(String)
    retweet_count = Column(Integer)
    like_count = Column(Integer)
    followers_count = Column(Integer)
    retweet_ratio = Column(Float)
    like_ratio = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AccountMetric(Base):
    __tablename__ = "account_metrics"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, index=True)
    followers_count = Column(Integer)
    tweet_count = Column(Integer)
    engagement_rate = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)