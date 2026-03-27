import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Azure OpenAI configuration
    AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    # JWT authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Upload and batch limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_BATCH_SIZE: int = 10
    MAX_INPUT_CHARS: int = 50000  # Truncate input text beyond this limit

    # Summary token budgets per length
    SUMMARY_LENGTHS: dict = {"short": 100, "medium": 300, "long": 600}

    # Retry settings for Azure OpenAI API calls
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))

    # Server settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")

    @property
    def azure_openai_configured(self) -> bool:
        return bool(self.AZURE_OPENAI_KEY and self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_DEPLOYMENT)


settings = Settings()
