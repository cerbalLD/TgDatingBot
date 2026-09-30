from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def profile_menu(is_enabled: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад", callback_data="user:profile_menu:back"
                ),
                InlineKeyboardButton(
                    text="Изменить", callback_data="user:profile_menu:edit"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отключить анкету" if is_enabled else "Включить анкету",
                    callback_data="user:profile_menu:disable",
                )
            ],
        ]
    )


def profile_edit_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Фото", callback_data="user:profile_edit:photo"
                ),
                InlineKeyboardButton(
                    text="Имя", callback_data="user:profile_edit:name"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Возраст", callback_data="user:profile_edit:age"
                ),
                InlineKeyboardButton(
                    text="Пол", callback_data="user:profile_edit:sex"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Город", callback_data="user:profile_edit:city"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Сфера деятельности:", callback_data="user:profile_edit:q1"
                ),
                InlineKeyboardButton(
                    text="Увлечения и хобби:", callback_data="user:profile_edit:q2"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Какого партнера хочеться встретить: ", callback_data="user:profile_edit:q3"
                ),
                InlineKeyboardButton(
                    text="Семейное положение:", callback_data="user:profile_edit:q4"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Заполнить заново", callback_data="user:profile_edit:reset"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад", callback_data="user:profile_edit:back"
                ),
            ],
        ]
    )
