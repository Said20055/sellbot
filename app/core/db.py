from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings

# Создаем асинхронный движок
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Фабрика для создания асинхронных сессий
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session