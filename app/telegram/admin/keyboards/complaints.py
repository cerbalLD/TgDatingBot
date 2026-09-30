from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def profile_complaint_keyboard(complaint_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Бан", callback_data=f"admin:complaint:ban:{complaint_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Пропустить", callback_data=f"admin:complaint:skip:{complaint_id}"
                )
            ]
        ]
    )


def complaint_ban_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Не отправлять", callback_data="admin:complaint:ban:skip"
                )
            ]
        ]
    )
