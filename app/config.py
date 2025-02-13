# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из файла .env, если он присутствует

class Config:
    # Конфигурация для Twitter (используется в будущем)
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    
    # Конфигурация для OpenAI (LLM)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Конфигурация для подключения к PostgreSQL
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")
    
    # Начальные параметры проекта
    NICHE = os.getenv("NICHE", "Meme Coins")
    STYLE = os.getenv("STYLE", "Humorous")
    RULES = os.getenv("RULES", "Строгий контроль качества контента")