from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.1  # low temperature for clinical consistency

    # ChromaDB
    chroma_persist_dir: str = "chroma_db"
    chroma_collection_name: str = "triage_knowledge_base"

    # RAG
    rag_top_k: int = 5
    rag_chunk_size: int = 400
    rag_chunk_overlap: int = 80

    # App
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def __repr__(self) -> str:
        masked_key = f"...{self.openai_api_key[-4:]}" if self.openai_api_key else "not set"
        return (
            f"AppConfig(openai_api_key={masked_key!r}, "
            f"openai_model={self.openai_model!r}, "
            f"environment={self.environment!r})"
        )


config = AppConfig()
