import asyncio
import datetime

class RecommendationModule:
    """
    Модуль генерации рекомендаций:
      - Принимает данные аналитики Twitter и, при необходимости, данные из базы.
      - Генерирует рекомендации по:
          * Какому твиту отдать приоритет для ретвита.
          * На кого подписаться (например, авторов виральных твитов).
          * Оптимальному времени для публикации твита.
          * Теме для нового твита.
    """
    def __init__(self, config: dict):
        self.config = config

    async def generate_recommendation(self, analytics_data: dict) -> dict:
        recommendation = {}
        viral_tweets = analytics_data.get("viral_tweets", [])
        if viral_tweets:
            # Выбираем твит с максимальным retweet_ratio как лучший пример
            best_tweet = max(viral_tweets, key=lambda t: t['retweet_ratio'])
            recommendation["retweet"] = {
                "tweet_id": best_tweet['tweet_id'],
                "text": best_tweet['text']
            }
            recommendation["follow"] = f"""Подпишитесь на автора твита {best_tweet['tweet_id']}"""
        else:
            recommendation["retweet"] = None
            recommendation["follow"] = None

        # Рекомендуем оптимальное время: текущие время + 1 час (пример)
        optimal_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        recommendation["optimal_tweet_time"] = optimal_time.isoformat() + "Z"
        recommendation["tweet_topic"] = "Обсудите последние тренды крипто-мира и мем-койнов."
        return recommendation
