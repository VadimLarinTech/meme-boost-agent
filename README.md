# Meme Boost Agent

Meme Boost Agent (powered by Venice) is an adaptive AI-driven Twitter agent designed to generate high-quality, viral-worthy content and images (memes) tailored to a specific niche. The agent continuously monitors Twitter data, analyzes engagement metrics, and adapts its behavior over time to maximize audience growth and engagement. It also provides actionable recommendations for social media management.

## Overview

The Meme Boost Agent is built to serve individual meme developers, small teams, and artists involved in meme promotion. It focuses on:

- Generating potentially viral tweets and images.
- Monitoring account performance and engagement.
- Adapting its behavior based on aggregated analytics and feedback.
- Providing recommendations on actions (e.g., retweets, follows) that help increase audience engagement and growth.

## Architecture

The project is composed of two main parts:
### 1. Agent Core

- Control Module (Controller):
    Based on LangChain and an LLM model, it manages the main working cycle of the agent.
- Analytics and Metrics Module:
    Continuously monitors key performance metrics (e.g., engagement, account dynamics) and analyzes them.
- Adaptation Module:
    Evaluates how the agent’s actions affect results and makes adjustments (e.g., modifies prompts).
- Strategic Module:
    Determines the long-term direction of the agent.

During initialization, the agent is configured with:

- The niche in which it will operate.
- The target audience.
- The brand name.
- The behavioral style.
- The current goal (e.g., audience growth, engagement, prompting a target action).

### 2. Business Logic

Consists of three main modules:

- Twitter Analytics Module:
    Identifies viral tweets within the specified niche by filtering and analyzing tweets via an LLM and saves the results in the database.
- Content Creation Module:
    Generates potentially viral tweets based on viral tweet samples and the agent's strategy. It also produces images using the Venice.ai API. In image generation, the prompt is built around the brand name (the primary focus), with additional user prompt variations.
- Recommendations Module:
    Suggests actionable steps (e.g., which tweet to retweet, whom to follow, optimal posting time, tweet topics) to achieve the agent's strategic goals. Engagement (retweets, likes, follows) is key until the account reaches its first thousand followers.
- Performance Tracking Module:
    Runs daily to collect Twitter account metrics (e.g., followers, tweet count, engagement) and saves them for further analysis.

## Features

- Adaptive Workflow:
    The core engine continuously runs a cycle, aggregates data, and triggers a weekly adaptation process that updates system settings.
- Real-Time Analytics:
    Continuously collects and processes Twitter data to identify and analyze viral tweets.
- Content Generation:
    Produces text content and images that strictly adhere to preset requirements, with the brand name being the primary focus.
- Actionable Recommendations:
    Provides suggestions to optimize social media engagement.
- Background Tasks:
    Runs background processes for tweet analytics, daily metrics collection, and weekly adaptation.
- User API:
    Exposes endpoints for aggregated analytics, content creation, recommendations, performance metrics, and adaptation logs.
- Dashboard (Planned):
    A UI dashboard to visualize viral tweets and analytics data.

## Installation and Setup
### Prerequisites

- Python 3.9 or higher
- PostgreSQL database
- Required API keys for Twitter, OpenAI, and Venice.ai

### Installation Steps

1. Clone the Repository:
```
git clone https://github.com/VadimLarinTech/meme-boost-agent
cd meme-boost-agent
```

2. Create and Activate a Virtual Environment:
```
python -m venv venv
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```
3. Install Dependencies:
```
pip install -r requirements.txt
```
4. Set Up the Database:
Ensure that PostgreSQL is running and that you have created the database and user as specified in your configuration. For testing, the application can create the tables automatically. In production, use proper migration tools (e.g., Alembic).
5. Create the ```.env``` File:
```
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_BEARER_TOKEN=
TWITTER_QUERY=
TWITTER_ACCOUNT_ID=
OPENAI_API_KEY=
DATABASE_URL=
NICHE=
STYLE=
RULES=
BRAND_NAME=
GOALS=
ADAPTATION_INTERVAL=
MAX_VIRAL_TWEETS=
```

## Running the Project

To run the project, use Uvicorn from the project root:
```
uvicorn app.main:app --reload
```

This will start the FastAPI server and, on startup, launch background tasks for:

- Tweet analytics (runs every 5 minutes)
- Daily performance metrics collection
- Weekly adaptation cycle
- The AgentCore main cycle

## API Endpoints

The API exposes the following endpoints:

- GET /analytics:
    Returns aggregated analytics data (viral tweets, metrics, adaptation logs) from the past 7 days.

- POST /generate_content:
    Accepts a user prompt (optional) and returns generated tweet content that adheres to the preset requirements.

- GET /recommendations:
    Provides actionable recommendations (e.g., which tweet to retweet, whom to follow, optimal posting time, tweet topic) based on the aggregated Twitter data.

- GET /performance:
    Returns the latest Twitter account metrics.

- GET /adaptation_logs:
    Returns adaptation logs for the past 7 days.

- GET /generate_image:
    Generates an image using Venice.ai API based on project parameters and an optional additional prompt.

These endpoints are documented via Swagger UI, available at:
```http://localhost:8000/docs```

## Background Tasks

The project uses asynchronous background tasks to ensure continuous operation:

- Twitter Analytics Background Task:
    Runs every 5 minutes to fetch and analyze tweets. It aggregates viral tweets and stores them in the database, applying duplicate filtering and switching between multiple Twitter API keys to avoid rate limits.

- Performance Tracking Background Task:
    Runs daily to fetch Twitter account metrics and store them in the database.

- Weekly Adaptation Task:
    Aggregates data from viral tweets, performance metrics, and adaptation logs over the adaptation interval (e.g., 7 days). It then uses an LLM (via LangChain) to generate updated adaptive settings, which are stored in the database and influence the behavior of business modules.

## License
Proprietary License Agreement