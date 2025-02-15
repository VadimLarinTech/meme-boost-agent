from fastapi import FastAPI
import asyncio
from app.api.endpoints import router as api_router
from app.core.agent_core import AgentCore
from app.background_tasks import run_twitter_analytics_background, run_performance_tracking_background, run_weekly_adaptation
from app.db.models import Base
from app.db.models import engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(api_router)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # origins        
    allow_credentials=True,       
    allow_methods=["*"],          
    allow_headers=["*"],          
)

agent_core = AgentCore()

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Run main cycle
    asyncio.create_task(agent_core.run_cycle())
    # Background tasks
    asyncio.create_task(run_twitter_analytics_background())
    asyncio.create_task(run_performance_tracking_background())
    asyncio.create_task(run_weekly_adaptation())

