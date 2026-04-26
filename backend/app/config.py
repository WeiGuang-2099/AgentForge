"""Application configuration."""
from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM 提供商配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    GOOGLE_API_KEY: Optional[str] = None
    ZHIPUAI_API_KEY: Optional[str] = None  # 智谱 AI API Key
    DEEPSEEK_API_KEY: Optional[str] = None  # DeepSeek API Key
    MOONSHOT_API_KEY: Optional[str] = None  # Moonshot API Key
    
    # 自定义 API 端点
    OPENAI_API_BASE: Optional[str] = None
    ANTHROPIC_API_BASE: Optional[str] = None
    ZHIPUAI_API_BASE: Optional[str] = None
    DEEPSEEK_API_BASE: Optional[str] = None
    MOONSHOT_API_BASE: Optional[str] = None
    
    # 应用配置
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production"
    APP_DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://agentforge:password@localhost:5432/agentforge"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 向量数据库
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # 工具配置
    SERPER_API_KEY: Optional[str] = None
    BING_API_KEY: Optional[str] = None
    
    # 功能开关
    ENABLE_CODE_EXECUTION: bool = True
    ENABLE_WEB_SEARCH: bool = True
    ENABLE_FILE_OPS: bool = True

    # Memory settings
    ENABLE_MEMORY: bool = True
    MEMORY_SHORT_TERM_WINDOW: int = 20
    MEMORY_LONG_TERM_TOP_K: int = 5
    
    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # 速率限制
    RATE_LIMIT_PER_MINUTE: int = 30

    # 语言和地区
    DEFAULT_LANGUAGE: str = "zh-CN"
    TIMEZONE: str = "Asia/Shanghai"

    @model_validator(mode='after')
    def _check_secret_key(self):
        if self.APP_SECRET_KEY == "change-me-in-production" and self.APP_ENV == "production":
            raise ValueError(
                "APP_SECRET_KEY must be changed from its default value in production"
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
