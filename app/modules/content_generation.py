import asyncio
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from sqlalchemy import select
from app.db.models import ViralTweet

class ContentGenerationModule:
    """
    Модуль генерации контента:
      - Использует LangChain для создания цепочки запросов к LLM (например, OpenAI).
      - Генерирует текстовые твиты, учитывая примеры виральных твитов, сохранённых в базе.
      - Содержит заглушку для генерации изображений с использованием внешней бесплатной модели.
    """
    def __init__(self, config: dict, db_session_maker):
        self.config = config
        self.db_session_maker = db_session_maker
        self.llm = OpenAI(api_key=self.config.OPENAI_API_KEY, temperature=0.7)
        self.prompt_template = PromptTemplate(
            template=(
                "Сгенерируй твит для мем-койна в стиле {style}.\n"
                "Примеры виральных твитов:\n{viral_examples}\n"
                "Дополнительный запрос: {prompt}"
            ),
            input_variables=["style", "viral_examples", "prompt"]
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    async def get_viral_examples(self, limit: int = 3) -> str:
        """
        Извлекает примеры виральных твитов из базы данных для включения в промпт.
        """
        viral_examples = []
        async with self.db_session_maker() as session:
            result = await session.execute(
                select(ViralTweet).order_by(ViralTweet.retweet_ratio.desc()).limit(limit)
            )
            tweets = result.scalars().all()
            for tweet in tweets:
                viral_examples.append(tweet.text)
        return "\n---\n".join(viral_examples)

    async def generate_content(self, prompt: str) -> str:
        """
        Генерирует текстовый контент по запросу пользователя с учетом примеров виральных твитов.
        """
        viral_examples = await self.get_viral_examples()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.chain.run,
            {"style": self.config.STYLE, "viral_examples": viral_examples, "prompt": prompt}
        )
        return result

    async def generate_image(self, prompt: str) -> str:
        """
        Заглушка для генерации изображения.
        Здесь можно интегрировать вызов внешней бесплатной генеративной модели (например, Stable Diffusion API).
        """
        # Реальная интеграция будет включать отправку запроса к API генерации изображений
        await asyncio.sleep(0)  # Без задержки в данном MVP
        return f"Сгенерированное изображение для запроса: {prompt}"
