from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.repository import Repository

# --- НОВАЯ ГЛАВНАЯ КЛАВИАТУРА ---
def main_menu_keyboard(user_id: int, admin_ids: list):
    buttons = [
        [InlineKeyboardButton(text="🛒 Купить товар", callback_data="show_products")],
        
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/MagicShop_Support")]
    ]
    if user_id in admin_ids:
        buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- НОВАЯ КЛАВИАТУРА ДЛЯ СПИСКА ТОВАРОВ ---
async def product_list_keyboard(repo: Repository):
    buttons = []
    products = await repo.get_all_products()
    
    for product in products:
        # Цена уже в рублях, просто форматируем
        button_text = f"{product.name} - {product.price:.2f} руб."
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"product_{product.product_id}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для админ-панели (без изменений)
def admin_panel_keyboard():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="delete_product_list")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def products_for_delete_keyboard(repo: Repository):
    buttons = []
    products = await repo.get_all_products()
    for product in products:
        buttons.append([InlineKeyboardButton(text=f"❌ {product.name}", callback_data=f"del_product_{product.product_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def reply_to_user_keyboard(order_id: int, user_id: int):
    # Добавляем user_id в callback для прямого ответа
    button = InlineKeyboardButton(text="✍️ Ответить пользователю", callback_data=f"reply_user_{order_id}_{user_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])

def reply_to_admin_keyboard(order_id: int):
    button = InlineKeyboardButton(text="✍️ Ответить администратору", callback_data=f"reply_admin_{order_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])

def order_user_keyboard(order_id: int):
    button1 = InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order_by_user")
    button2 = InlineKeyboardButton(text="✍️ Написать администратору", callback_data=f"reply_admin_{order_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])