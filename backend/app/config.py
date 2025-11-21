from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "resonant"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "resonant_dashboard"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
