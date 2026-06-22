from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    supervisor_model: str = "deepseek-v4-pro"
    explainer_model: str = "deepseek-v4-flash"
    quizzer_model: str = "deepseek-v4-pro"
    checker_model: str = "deepseek-v4-flash"
    recommender_model: str = "deepseek-v4-flash"

    # Embedding (may use a different provider than LLM)
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str | None = None  # None → use OpenAI default

    # Database
    database_url: str = "postgresql+asyncpg://agent:agent123@localhost:5432/agent_learning"
    database_url_sync: str = "postgresql+psycopg2://agent:agent123@localhost:5432/agent_learning"

    # Tavily
    tavily_api_key: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
