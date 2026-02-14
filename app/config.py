from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Multi-Agent Code Explainer"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"


    # Model routing (multi-agent)
    FAST_MODEL: str = "llama3.2:1b"
    POWERFUL_MODEL: str = "llama3.2:3b"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"  # default
    OLLAMA_TIMEOUT: int = 120

    # LLM params
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 512

    # Embedding / RAG
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DB_PATH: str = "./data/vectordb"
    DOCUMENTS_PATH: str = "./data/documents"
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80
    TOP_K_RESULTS: int = 3

    # (Opsiyonel) RAG filtre eşiği
    MIN_RELEVANCE_SCORE: float = 0.0

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
