import asyncio
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from sqlalchemy import select
from app.db.models import ViralTweet, AdaptationSettings
from app.config import Config
from app.db.models import async_session as db_session_maker

class ContentGenerationModule:
    """
    Content Generation Module:
      - Uses LangChain to build a chain for generating new tweet content.
      - Retrieves viral tweet examples with analysis from the database.
      - Uses adaptation settings to update the style.
      - Provides a placeholder for image generation.
    """
    def __init__(self):
        self.style = Config.STYLE
        self.niche = Config.NICHE
        self.rules = Config.RULES
        self.brand_name = Config.BRAND_NAME 
        self.goals = Config.GOALS 
        self.correction = "" 
        self.llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, temperature=0.7, model_name="gpt-4o")
        self.prompt_template = PromptTemplate(
            template=(
                "Generate a tweet for a meme coin with the following hard requirements:\n"
                "Niche: {niche}\n"
                "Style: {style}\n"
                "Rules: {rules}\n"
                "Brand Name: {brand_name}\n"
                "Goals (the primary and highest priority): {goals}\n"
                "IMPORTANT: If the 'Goals' field does not specify any commercial objective, under no circumstances generate tweets that propose to buy, sell, or promote any product or service.\n"
                "Note: The examples below are samples and must not conflict with the Goals. "
                "The content must not blatantly lie except when it is clearly intended as a joke or irony.\n\n"
                "Examples of viral tweets with analysis:\n{viral_examples}\n\n"
                "Additional prompt: {prompt}"
            ),
            input_variables=["niche", "style", "rules", "brand_name", "goals", "viral_examples", "prompt"]

        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    async def update_parameters(self):
        async with db_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(select(AdaptationSettings))
            settings = result.scalar_one_or_none()
            if settings:
                self.style = settings.generation_style
                self.correction = settings.correction if hasattr(settings, 'correction') else ""
            else:
                self.correction = ""

    async def get_viral_examples(self, limit: int = 3) -> str:
        viral_examples = []
        async with db_session_maker() as session:
            result = await session.execute(
                select(ViralTweet).order_by(ViralTweet.retweet_ratio.desc()).limit(limit)
            )
            tweets = result.scalars().all()
            for tweet in tweets:
                analysis_text = getattr(tweet, 'analysis', 'No analysis available')
                example = f"Tweet: {tweet.text}\nAnalysis: {analysis_text}"
                viral_examples.append(example)
        return "\n---\n".join(viral_examples)

    async def generate_content(self, prompt: str) -> str:
        await self.update_parameters()
        viral_examples = await self.get_viral_examples()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.chain.run,
            {
                "niche": self.niche,
                "style": self.style,
                "rules": self.rules,
                "brand_name": self.brand_name,
                "goals": self.goals,
                "viral_examples": viral_examples,
                "prompt": prompt
            }
        )
        return result

    async def generate_image(self, prompt: str) -> str:
        from app.modules.image_generator import VeniceImageGenerator
        
        generator = VeniceImageGenerator()
        image_url = await generator.generate_image(prompt, self.correction)
        return image_url
