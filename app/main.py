import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.config import settings
from core.db import engine
from models.models import Base
from handlers import common, user_handlers, admin_handlers
from middlewares.db import DbSessionMiddleware

# Функция для создания таблиц в БД
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def set_bot_commands(bot: Bot):
    """
    Устанавливает команды для бота в меню Telegram.
    """
    commands = [
        BotCommand(
            command="start",
            description="Главное меню 🏠"
        )
        # Сюда можно добавить другие команды, если они появятся
        # BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)
    
async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    # Даем БД немного времени на "прогрев"
    await asyncio.sleep(5) 

    # --- Создаем таблицы перед запуском бота ---
    logging.info("Creating database tables...")
    await create_tables()
    logging.info("Tables created successfully.")
    # -------------------------------------------

    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    dp.update.middleware(DbSessionMiddleware(session_pool=session_maker))

    dp.include_router(common.router)
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")