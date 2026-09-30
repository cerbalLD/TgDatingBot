from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def likes_queue_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Лайк", callback_data=f"user:likes:like:{target_user_id}"
                ),
                InlineKeyboardButton(
                    text="Дизлайк", callback_data=f"user:likes:dislike:{target_user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Пожаловаться", callback_data=f"user:complaint:profile:{target_user_id}"
                )
            ]
        ]
    )
