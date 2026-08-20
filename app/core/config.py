from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    GROQ_API_KEY: str = Field(..., validation_alias="GROQ_API_KEY")
    HF_TOKEN: str = ""
    LLM_MODEL: str = "llama-3.1-8b-instant" 
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_DB_PATH: str = "./chroma_db"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()