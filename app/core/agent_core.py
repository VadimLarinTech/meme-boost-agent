# app/core/agent_core.py
import asyncio
import logging

from app.config import Config
from app.db.models import Metric
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AgentCore:
    def __init__(self, config: Config):
        self.config = config
        self.loop = asyncio.get_event_loop()
        
        # Инициализация подключения к БД для сохранения метрик
        self.engine = create_async_engine(self.config.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Инициализация LangChain для адаптации
        self.llm = OpenAI(api_key=self.config.OPENAI_API_KEY, temperature=0.7)
        prompt_template = f"""
            Собери информацию о следующих метриках:
            {metrics}
            На основе этих данных, предложи корректировки для улучшения работы ИИ-агента.
            """
        self.prompt = PromptTemplate(template=prompt_template, input_variables=["metrics"])
        self.adaptation_chain = LLMChain(llm=self.llm, prompt=self.prompt)
        
        # Здесь будут подключаться бизнес-модули (пока заглушки)
        self.twitter_analytics_module = None  # TODO: Реализовать в будущем
        self.content_generation_module = None  # TODO: Реализовать в будущем
        self.recommendation_module = None  # TODO: Реализовать в будущем
        
        # Временное накопление данных по циклам для адаптации
        self.cycle_data = []

    async def log_metric(self, name: str, value: float):
        async with self.async_session() as session:
            metric = Metric(name=name, value=value)
            session.add(metric)
            await session.commit()
            logger.info(f"[DB] Logged metric: {name} = {value}")

    async def gather_metrics(self):
        f"""
        Здесь симулируется сбор метрик.
        В реальном проекте метрики будут собираться из бизнес-модулей и
        другими средствами мониторинга.
        """
        # Пример набора метрик (значения – заглушки)
        metrics = {
            "twitter_sentiment": 0.8,
            "tweet_volume": 1500,
            "engagement_rate": 0.05
        }
        return metrics

    async def run_cycle(self):
        f"""
        Основной цикл работы агента.
          0. Инициализация проекта (однократно при старте).
          1. Постоянный сбор данных (аналитика Twitter и др.) — работает постоянно.
          2. Генерация рекомендаций по активности (по запросу или циклически).
          3. Адаптация: накапливание метрик, агрегация и вызов цепочки LangChain для адаптации.
          4. Стратегический анализ — планируется для долгосрочных корректировок.
        """
        # Нулевой шаг: инициализация проекта
        logger.info("Инициализация проекта:")
        logger.info(f"Ниша: {self.config.NICHE}, Стиль: {self.config.STYLE}, Правила: {self.config.RULES}")
        
        # Основной цикл работы (бесконечный цикл)
        while True:
            logger.info("Запуск цикла работы агента")
            
            # 1. Сбор аналитики (пока симулированная заглушка)
            twitter_data = {"dummy": "data"}  # TODO: заменить на вызов self.twitter_analytics_module.fetch_data()
            logger.info("Получены данные аналитики Twitter: %s", twitter_data)
            
            # 2. Генерация рекомендаций (вызывается по запросу — здесь просто заглушка)
            recommendation = "Рекомендуется ретвитнуть позитивный пост"  # TODO: заменить на self.recommendation_module.generate()
            logger.info("Сгенерированные рекомендации: %s", recommendation)
            
            # 3. Сбор и накопление метрик
            metrics = await self.gather_metrics()
            self.cycle_data.append(metrics)
            for name, value in metrics.items():
                await self.log_metric(name, value)
            
            # 4. Если накоплено достаточное число циклов (например, 3 цикла), запускаем адаптацию
            if len(self.cycle_data) >= 3:
                aggregated_metrics = self.aggregate_metrics(self.cycle_data)
                logger.info("Агрегированные метрики: %s", aggregated_metrics)
                adaptation_suggestion = await self.adaptation_chain.run({"metrics": str(aggregated_metrics)})
                logger.info("Рекомендация по адаптации от LLM: %s", adaptation_suggestion)
                # Здесь можно реализовать корректировку параметров агента
                self.cycle_data = []  # Сброс накопленных данных после адаптации
            
            # 5. Стратегическое планирование (пока отложено; планируется для более длительных интервалов)
            # TODO: Добавить вызов стратегического модуля
            
            # Пауза между циклами (например, 30 секунд)
            await asyncio.sleep(30)

    def aggregate_metrics(self, metrics_list):
        f"""
        Простейшая функция для агрегирования метрик:
        Вычисляет среднее значение для каждой метрики.
        """
        aggregated = {}
        count = len(metrics_list)
        for metrics in metrics_list:
            for key, value in metrics.items():
                aggregated.setdefault(key, 0)
                aggregated[key] += value
        for key in aggregated:
            aggregated[key] /= count
        return aggregated

    def start(self):
        try:
            self.loop.run_until_complete(self.run_cycle())
        except KeyboardInterrupt:
            logger.info("Агент остановлен пользователем.")


if __name__ == "__main__":
    from app.config import Config
    config = Config()
    agent = AgentCore(config)
    agent.start()
