from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Просто объявляем переменные, которые нужно прочитать из окружения.
    # Pydantic-settings сделает все остальное автоматически.
    BOT_TOKEN: str
    ADMIN_IDS: str 

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ADMIN_LIST(self) -> list[int]:
        # Этот код сработает, так как ADMIN_IDS теперь будет успешно загружен
        return [int(admin_id.strip()) for admin_id in self.ADMIN_IDS.split(',')]

settings = Settings()