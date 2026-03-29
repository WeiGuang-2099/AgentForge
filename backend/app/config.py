"""Application configuration."""
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
    
    # 语言和地区
    DEFAULT_LANGUAGE: str = "zh-CN"
    TIMEZONE: str = "Asia/Shanghai"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
