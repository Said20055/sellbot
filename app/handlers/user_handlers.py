import logging
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.common import send_welcome
from services.texts import WELCOME_TEXT
from models.models import Product
from services.repository import Repository
# --- ОБНОВЛЯЕМ ИМПОРТЫ КЛАВИАТУР ---
from keyboards.inline import (
    product_list_keyboard,
    reply_to_user_keyboard,
    reply_to_admin_keyboard
)
from core.config import settings

router = Router()

# FSM для ответа администратору по заявке
class ReplyToAdmin(StatesGroup):
    waiting_for_message = State()



# --- НАВИГАЦИЯ ПО МЕНЮ ---

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery, bot: Bot):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

    await send_welcome(callback.from_user.id, bot, settings)
    await callback.answer()


@router.callback_query(F.data == "show_products")
async def show_product_list(callback: CallbackQuery, session: AsyncSession):
    repo = Repository(session)

    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

    # Отправляем новое сообщение
    await callback.message.answer(
        "Выберите товар для покупки:",
        reply_markup=await product_list_keyboard(repo)
    )

    # Обязательно подтверждаем callback, чтобы не было "часиков" у пользователя
    await callback.answer()


# --- ЛОГИКА ПОКУПКИ ТОВАРА ---

@router.callback_query(F.data.startswith("product_"))
async def create_order(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    # Отвечаем на нажатие кнопки, чтобы убрать "часики"
    await callback.answer("Создаем вашу заявку...")
    
    # Получаем ID товара и информацию о пользователе
    product_id = int(callback.data.split("_")[1])
    user = callback.from_user
    repo = Repository(session)

    # 1. Создаем заказ в базе данных
    order = await repo.create_order(user_id=user.id, product_id=product_id)
    
    # 2. Получаем полную информацию о товаре для уведомления
    product = await repo.session.get(Product, product_id)
    
    # 3. Готовим текст сообщения для администратора
    price_rub = product.price if product else 0
    admin_text = (f"🚨 <b>Новая заявка №{order.order_id}</b>\n\n"
                  f"<b>От:</b> {user.full_name}\n"
                  f"<b>Username:</b> @{user.username or 'не указан'}\n"
                  f"<b>User ID:</b> <code>{user.id}</code>\n\n"
                  f"<b>Товар:</b> {product.name if product else 'Неизвестный товар'}\n"
                  f"<b>Цена:</b> {price_rub:.2f} руб.")
    
    # 4. Пытаемся отправить уведомление каждому администратору
    for admin_id in settings.ADMIN_LIST:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=reply_to_user_keyboard(order.order_id, user.id)
            )
        except Exception as e:
            # Если отправить не удалось, мы увидим ошибку в консоли
            logging.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
            
    # 5. Отправляем подтверждение пользователю (этот код выполнится в любом случае)
    user_text = (f"✅ <b>Ваша заявка №{order.order_id} успешно создана!</b>\n\n"
                 f"<b>Товар:</b> {product.name if product else 'Неизвестный товар'}\n"
                 f"<b>Цена:</b> {price_rub:.2f} руб.\n\n"
                 f"Администратор скоро с вами свяжется. Если хотите что-то уточнить или добавить к заявке, нажмите кнопку ниже.")

    await callback.message.edit_text(
        text=user_text,
        reply_markup=reply_to_admin_keyboard(order.order_id)
    )

# --- Логика ответа администратору ---

@router.callback_query(F.data.startswith("reply_admin_"))
async def reply_to_admin_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    await state.set_state(ReplyToAdmin.waiting_for_message)
    await state.update_data(order_id=order_id)
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите ваше сообщение для администратора:")
    await callback.answer()

@router.message(ReplyToAdmin.waiting_for_message)
async def send_reply_to_admin(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data['order_id']
    user = message.from_user
    
    info_header = (f"💬 Сообщение от пользователя по заявке №{order_id}\n\n"
                   f"<b>От:</b> {user.full_name} (@{user.username or 'не указан'})\n"
                   f"<b>User ID:</b> <code>{user.id}</code>")

    reply_kb = reply_to_user_keyboard(order_id, user.id)

    for admin_id in settings.ADMIN_LIST:
        try:
            # --- НОВАЯ ЛОГИКА IF/ELSE ---
            # ЕСЛИ СООБЩЕНИЕ - ЭТО ПРОСТО ТЕКСТ
            if message.content_type == ContentType.TEXT:
                # Отправляем ОДНО комбинированное сообщение
                full_text = f"{info_header}\n\n<b>Сообщение:</b>\n<blockquote>{message.text}</blockquote>"
                await bot.send_message(chat_id=admin_id, text=full_text, reply_markup=reply_kb)
            
            # ЕСЛИ СООБЩЕНИЕ - ЭТО ФОТО, ДОКУМЕНТ, ВИДЕО И Т.Д.
            else:
                # Отправляем ДВА сообщения: сначала "шапку", потом сам файл
                await bot.send_message(chat_id=admin_id, text=info_header)
                await message.copy_to(chat_id=admin_id, reply_markup=reply_kb)

        except Exception as e:
            logging.error(f"Не удалось переслать сообщение админу {admin_id}: {e}")

    await message.answer(
        "✅ Ваше сообщение отправлено администратору.",
        reply_markup=reply_to_admin_keyboard(order_id)
    )
    await state.clear()
