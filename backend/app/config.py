from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_API_KEY: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    DATABASE_URL: str

    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # .env 파일을 불러와서 설정값을 설정합니다.