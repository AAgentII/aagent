import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import json


class Settings(BaseSettings):
    # API Keys
    claude_api_key: str = Field(..., env='CLAUDE_API_KEY')
    claude_api_base_url: str = Field(..., env='CLAUDE_API_BASE_URL')
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')
    
    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    redis_url: str = Field(..., env='REDIS_URL')
    
    # Security
    secret_key: str = Field(..., env='SECRET_KEY')
    algorithm: str = Field(default="HS256", env='ALGORITHM')
    access_token_expire_minutes: int = Field(default=30, env='ACCESS_TOKEN_EXPIRE_MINUTES')
    
    # Vector Database
    qdrant_host: str = Field(default="localhost", env='QDRANT_HOST')
    qdrant_port: int = Field(default=6333, env='QDRANT_PORT')
    qdrant_api_key: Optional[str] = Field(None, env='QDRANT_API_KEY')
    
    # Application
    app_name: str = Field(default="Multi-Agent Orchestration System", env='APP_NAME')
    app_version: str = Field(default="1.0.0", env='APP_VERSION')
    debug: bool = Field(default=False, env='DEBUG')
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env='CORS_ORIGINS')
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env='ENABLE_METRICS')
    log_level: str = Field(default="INFO", env='LOG_LEVEL')
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, str):
            return json.loads(self.cors_origins)
        return self.cors_origins


# Create global settings instance
settings = Settings()