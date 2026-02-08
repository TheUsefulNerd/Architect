"""
Configuration management using Pydantic Settings.
Loads environment variables and provides type-safe configuration.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    groq_api_key: str = Field(..., description="Groq API key")
    
    # Qdrant Configuration
    qdrant_url: str = Field(..., description="Qdrant Cloud URL")
    qdrant_api_key: str = Field(..., description="Qdrant API key")
    
    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    supabase_service_key: str = Field(
        ..., 
        description="Supabase service role key (admin access)"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="", 
        description="Direct PostgreSQL connection string (optional)"
    )
    
    # Application Settings
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=True)
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000")
    
    # LLM Configuration
    default_llm_provider: str = Field(default="gemini")
    default_model: str = Field(default="gemini-1.5-pro")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048)
    
    # Vector Database Settings
    embedding_model: str = Field(default="models/embedding-001")
    vector_dimension: int = Field(default=768)
    
    # Web Scraping Settings
    max_scrape_depth: int = Field(default=2)
    request_timeout: int = Field(default=30)
    user_agent: str = Field(default="Architect-Bot/1.0")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()