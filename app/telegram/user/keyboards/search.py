from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def limit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подписка", callback_data="user:main_menu:paysub"
                )
            ],
        ]
    )


def search_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Лайк", callback_data=f"user:search:like:{target_user_id}"
                ),
                InlineKeyboardButton(
                    text="Дизлайк", callback_data=f"user:search:dislike:{target_user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Пожаловаться", callback_data=f"user:complaint:profile:{target_user_id}"
                )
            ],
        ]
    )
