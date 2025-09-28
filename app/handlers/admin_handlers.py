from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.enums import ContentType

from services.repository import Repository
from keyboards.inline import admin_panel_keyboard, products_for_delete_keyboard, reply_to_admin_keyboard, reply_to_user_keyboard
from core.config import settings

router = Router()
router.message.filter(F.from_user.id.in_(settings.ADMIN_LIST))
router.callback_query.filter(F.from_user.id.in_(settings.ADMIN_LIST))

# --- ИЗМЕНЕНИЯ В FSM ---
class AddProduct(StatesGroup):
    name = State()
    price = State() # Вместо description

class ReplyToUser(StatesGroup):
    waiting_for_message = State()


# --- Управление Админ-панелью ---

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        "Вы в админ-панели. Выберите действие:",
        reply_markup=admin_panel_keyboard()
    )

# --- Логика добавления товара ---

@router.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.name)
    await callback.message.edit_text("Введите название нового товара:")
    await callback.answer()

@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Отлично. Теперь введите цену товара в рублях (например: 150.50 или 200):")

@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext, session: AsyncSession):
    try:
        # Пробуем конвертировать в число с плавающей точкой
        price_rub = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Цена должна быть числом. Пожалуйста, введите цену в рублях:")
        return

    data = await state.get_data()
    repo = Repository(session)
    
    await repo.add_product(name=data['name'], price=price_rub)
    
    await message.answer(f"✅ Товар '{data['name']}' с ценой {price_rub:.2f} руб. успешно добавлен!")
    await state.clear()
# --- Логика удаления товара ---

@router.callback_query(F.data == "delete_product_list")
async def delete_product_list(callback: CallbackQuery, session: AsyncSession):
    repo = Repository(session)
    await callback.message.edit_text(
        "Выберите товар для удаления:",
        reply_markup=await products_for_delete_keyboard(repo)
    )

@router.callback_query(F.data.startswith("del_product_"))
async def delete_product_confirm(callback: CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split("_")[2])
    repo = Repository(session)
    success = await repo.delete_product(product_id)
    if success:
        await callback.answer("✅ Товар удален.", show_alert=True)
        # Обновляем клавиатуру после удаления
        await callback.message.edit_text(
            "Выберите товар для удаления:",
            reply_markup=await products_for_delete_keyboard(repo)
        )
    else:
        await callback.answer("❌ Товар не найден.", show_alert=True)

# --- Логика ответа пользователю ---

@router.callback_query(F.data.startswith("reply_user_"))
async def reply_to_user_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])

    await state.set_state(ReplyToUser.waiting_for_message)
    await state.update_data(order_id=order_id, user_id=user_id)
    
    # Удаляем клавиатуру у сообщения админа, чтобы избежать повторных нажатий
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите ваш ответ пользователю:")
    await callback.answer()

@router.message(ReplyToUser.waiting_for_message)
async def send_reply_to_user(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = data['user_id']
    order_id = data['order_id']
    
    order_info = f"по заявке №{order_id}" if order_id != 0 else "по вашему обращению"
    reply_kb = reply_to_admin_keyboard(order_id)

    try:
        # --- НОВАЯ ЛОГИКА IF/ELSE ---
        # ЕСЛИ АДМИН ОТПРАВИЛ ПРОСТО ТЕКСТ
        if message.content_type == ContentType.TEXT:
            # Отправляем ОДНО красивое сообщение
            text = (f"Ответ от администратора {order_info}:\n\n"
                    f"<blockquote>{message.text}</blockquote>")
            await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_kb)
        
        # ЕСЛИ АДМИН ОТПРАВИЛ ФАЙЛ
        else:
            # Копируем файл, добавляя информацию в подпись к нему
            caption = f"Ответ от администратора {order_info}\n\n{message.caption or ''}"
            await message.copy_to(
                chat_id=user_id,
                caption=caption,
                reply_markup=reply_kb
            )

        await message.answer("✅ Ваш ответ успешно отправлен пользователю.")

    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение. Ошибка: {e}")
        
    await state.clear()