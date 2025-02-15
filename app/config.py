import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env if present

class Config:
    # Twitter configuration
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    TWITTER_BEARER_TOKEN_2 = os.getenv("TWITTER_BEARER_TOKEN_2")
    TWITTER_ACCOUNT_ID = os.getenv("TWITTER_ACCOUNT_ID")
    
    TWITTER_QUERY = os.getenv("TWITTER_QUERY")
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # PostgreSQL configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Project initial parameters
    VIRAL_THRESHOLD = float(os.getenv("VIRAL_THRESHOLD", "0.1"))
    NICHE = os.getenv("NICHE")
    STYLE = os.getenv("STYLE")
    RULES = os.getenv("RULES")
    BRAND_NAME = os.getenv("BRAND_NAME")
    GOALS = os.getenv("GOALS")
    
    # Adaptation interval in seconds (default 7 days)
    ADAPTATION_INTERVAL = int(os.getenv("ADAPTATION_INTERVAL", 604800))

    # Maximum number of viral tweets to consider during adaptation
    MAX_VIRAL_TWEETS = int(os.getenv("MAX_VIRAL_TWEETS", 100))

    PERFORMANCE_TRACKING_INTERVAL = int(os.getenv("PERFORMANCE_TRACKING_INTERVAL", 86400))

    VENICE_BASE_URL = os.getenv("VENICE_BASE_URL")
    VENICE_API_KEY = os.getenv("VENICE_API_KEY")
    VENICE_MODEL = os.getenv("VENICE_MODEL")
    STYLE_PRESET = os.getenv("STYLE_PRESET")