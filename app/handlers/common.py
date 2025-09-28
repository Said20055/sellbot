import logging
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from services.repository import Repository
from keyboards.inline import main_menu_keyboard # <-- Изменили импорт
from core.config import settings

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
        await bot.send_photo(
            chat_id=user.id,
            photo="AgACAgIAAxkBAAIBqWjY1ZnYG7tq6Qkc9H3zbDgenuYiAALI9TEb_zfJStPgQ55vrvuBAQADAgADeAADNgQ",
            caption="""<b>✨ Добро пожаловать в MagicShop! ✨</b>

Здесь вы найдете качественные товары по отличным ценам 🎁💎.
Если у вас возникнут вопросы — просто напишите нам, мы всегда готовы помочь 💬🤝"""
        )

        # Кнопки главного меню
        await message.answer(
            text="<i>Для начала выберите действие в меню ниже</i> ⬇️\n\n<b>Приятных покупок!</b> 🛍️🎉",
            reply_markup=main_menu_keyboard(user.id, settings.ADMIN_LIST)
        )
        return

    # Если пользователь уже существует
    await message.answer(
        text="""Вы находитесь в <b>главном меню</b> 🏠.  
Выберите нужное действие с помощью кнопок ниже ⬇️""",
        reply_markup=main_menu_keyboard(user.id, settings.ADMIN_LIST)
    )
        
        

