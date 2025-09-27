from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from services.repository import Repository
from keyboards.inline import main_menu_keyboard # <-- Изменили импорт
from core.config import settings

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    repo = Repository(session)
    await repo.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    await message.answer(
    text=f"""<b>✨ Добро пожаловать в MagicShop! ✨</b>
Здесь вы найдете качественные товары по отличным ценам 🎁💎.
Если у вас возникнут вопросы — просто напишите нам, мы всегда готовы помочь 💬🤝
<i>Для начала выберите действие в меню ниже</i> ⬇️
<b>Приятных покупок!</b> 🛍️🎉""",
    reply_markup=main_menu_keyboard(message.from_user.id, settings.ADMIN_LIST)
)