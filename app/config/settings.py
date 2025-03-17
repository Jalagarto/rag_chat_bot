"""
Configuración de la aplicación.
Carga variables de entorno y define parámetros de configuración.
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()

LLM = "gpt-4o-mini"

class Settings(BaseSettings):
    """Configuración centralizada de la aplicación usando Pydantic."""
    openai_api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""), env="OPENAI_API_KEY")
    
    embedding_model_name: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL_NAME")
    llm_model_name: str = Field(default=LLM, env="LLM_MODEL_NAME")
    summarizer_model_name: str = Field(default=LLM, env="SUMMARIZER_MODEL_NAME")
    
    # RAG
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    retrieval_k: int = Field(default=4, env="RETRIEVAL_K")
    
    max_memory_tokens: int = Field(default=2000, env="MAX_MEMORY_TOKENS")
    char_to_token_ratio: int = Field(default=4, env="CHAR_TO_TOKEN_RATIO")
    
    vector_db_path: str = Field(default="./data/chroma_db", env="VECTOR_DB_PATH")
    enable_vector_db_persistence: bool = Field(default=True, env="ENABLE_VECTOR_DB_PERSISTENCE")
    
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=7860, env="PORT")
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()