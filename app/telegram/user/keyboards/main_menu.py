from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu(is_created: bool = False, is_enabled: bool = True) -> InlineKeyboardMarkup:
    if is_created:
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text="🔍 Смотреть анкеты", callback_data="user:main_menu:search"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👤 Моя анкета", callback_data="user:main_menu:myprofile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❤️ Мои мэтчи", callback_data="user:main_menu:matches"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Подписка", callback_data="user:main_menu:paysub"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Поддержка", callback_data="user:main_menu:complaint"
                )
            ],
        ]
    else:
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text="👤 Создать анкету", callback_data="user:main_menu:createprofile"
                )
            ],
        ]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def start_continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Продолжить", callback_data="user:start:continue"
                )
            ]
        ]
    )


def start_data_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Согласен(а) — продолжить",
                    callback_data="user:start:data_consent",
                )
            ]
        ]
    )


def start_notifications_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Да, хочу", callback_data="user:start:notifications:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Пропустить", callback_data="user:start:notifications:skip"
                )
            ],
        ]
    )


def start_social_publish_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Согласен(а) — продолжить",
                    callback_data="user:start:social_publish",
                )
            ]
        ]
    )


def start_verification_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Согласен(а)", callback_data="user:start:verification:agree"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data="user:start:verification:cancel"
                )
            ],
        ]
    )
