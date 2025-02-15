import httpx
import asyncio
from app.config import Config
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

class VeniceImageGenerator:
    BASE_URL = Config.VENICE_BASE_URL

    def __init__(self):
        self.api_key = Config.VENICE_API_KEY  
        self.model = Config.VENICE_MODEL if hasattr(Config, "VENICE_MODEL") else "fluently-xl"
        self.llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, temperature=0.7, model_name="gpt-4o")
        self.prompt_template = PromptTemplate(
            template=(
                "Context: Brand: {brand_name}; Niche: {niche}; Style: {style}; Rules: {rules}; Goals: {goals}; Extra: {additional_prompt}.\n"
                "Correction: {correction}.\n"
                "Generate a concise image prompt using only essential keywords."
            ),
            input_variables=["brand_name", "niche", "style", "rules", "goals", "additional_prompt", "correction"]
            
        )
        self.prompt_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    async def generate_final_prompt(self, additional_prompt: str, correction: str = "") -> str:
        """
        Uses LLM to generate the final prompt for image generation.
        The final prompt emphasizes the BRAND_NAME and incorporates the additional prompt,
        while considering other project parameters only as secondary constraints.
        """
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            self.prompt_chain.run,
            {
                "brand_name": Config.BRAND_NAME,
                "niche": Config.NICHE,
                "style": Config.STYLE,
                "rules": Config.RULES,
                "goals": Config.GOALS,
                "additional_prompt": additional_prompt,
                "correction": correction
            }
        )
        return result.strip()

    async def generate_image(self, additional_prompt: str, correction: str = "") -> str:
        final_prompt = await self.generate_final_prompt(additional_prompt, correction)
        url = f"{self.BASE_URL}/image/generate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "width": 1024,
            "height": 1024,
            "steps": 30,
            "hide_watermark": False,
            "return_binary": False,
            "seed": 123,
        }
        if hasattr(Config, "VENICE_STYLE_PRESET") and Config.VENICE_STYLE_PRESET:
            payload["style_preset"] = Config.VENICE_STYLE_PRESET

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if "images" in data and isinstance(data["images"], list) and len(data["images"]) > 0:
                return data["images"][0]
            else:
                return "No image URL returned."
