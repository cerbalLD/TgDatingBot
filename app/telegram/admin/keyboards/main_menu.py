# telegram/keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_admin_panel(is_super: bool = False):
    inline_keyboard = [
        [
                InlineKeyboardButton(
                text="✅ Модерация анкет", callback_data="admin:panel:profiles"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Одобренные анкеты", callback_data="admin:panel:profiles:approved"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отклонённые анкеты", callback_data="admin:panel:profiles:rejected"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Обращения в поддержку", callback_data="admin:panel:support"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚠️ Жалобы пользователей", callback_data="admin:panel:complaints"
            )
        ],
        [
            InlineKeyboardButton(
                text="📨 Создать рассылку", callback_data="admin:panel:create_thread"
            )
        ],
    ]
    
    if is_super:
        inline_keyboard.append([
            InlineKeyboardButton(
                text="Добавить админа", callback_data="admin:panel:add_admin"
            )
        ])
        inline_keyboard.append([
            InlineKeyboardButton(
                text="Удалить админа", callback_data="admin:panel:remove_admin"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
