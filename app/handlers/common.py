import logging
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from services.texts import WELCOME_TEXT
from sqlalchemy.ext.asyncio import AsyncSession


from services.repository import Repository
from keyboards.inline import main_menu_keyboard # <-- Изменили импорт
from core.config import Settings, settings

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, bot):
    repo = Repository(session)
    user = message.from_user

    # Проверяем пользователя в БД
    is_new_user = await repo.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    # Если пользователь новый
    if is_new_user:
        admin_text = (f"👤 <b>Новый пользователь в боте!</b>\n\n"
                      f"<b>Имя:</b> {user.full_name}\n"
                      f"<b>Username:</b> @{user.username or 'не указан'}\n"
                      f"<b>User ID:</b> <code>{user.id}</code>")

        for admin_id in settings.ADMIN_LIST:
            try:
                await bot.send_message(admin_id, admin_text)
            except Exception:
                pass

        # Приветственное фото
    await send_welcome(message.from_user.id, bot, settings)
    return 


async def send_welcome(user_id: int, bot: Bot, settings: Settings):
    await bot.send_photo(
        chat_id=user_id,
        photo="AgACAgIAAxkBAAIBqWjY1ZnYG7tq6Qkc9H3zbDgenuYiAALI9TEb_zfJStPgQ55vrvuBAQADAgADeAADNgQ",
        caption=WELCOME_TEXT,
        reply_markup=main_menu_keyboard(user_id, settings.ADMIN_LIST)
    )
    return


