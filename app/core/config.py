from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"

    @property
    def DATABASE_URL(self):
        # ✅ PostgreSQL Async URL
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USERNAME}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"


settings = Settings()