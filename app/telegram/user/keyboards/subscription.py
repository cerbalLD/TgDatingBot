from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def subscription_keyboard(price_3_rub: int, price_7_rub: int, price_30_rub: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"3 дня за {price_3_rub} руб.",
                    callback_data="user:subscription:buy:3",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"7 дней за {price_7_rub} руб.",
                    callback_data="user:subscription:buy:7",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"30 дней за {price_30_rub} руб.",
                    callback_data="user:subscription:buy:30",
                )
            ],
        ]
    )
