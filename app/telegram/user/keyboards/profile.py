from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def sex_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Мужчина", callback_data=f"user:createprofile:{prefix}:male"
                ),
                InlineKeyboardButton(
                    text="Девушка", callback_data=f"user:createprofile:{prefix}:female"
                ),
            ]
        ]
    )


def find_sex_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчина", callback_data="user:createprofile:find_sex:male"),
                InlineKeyboardButton(text="Женщина", callback_data="user:createprofile:find_sex:female"),
                InlineKeyboardButton(text="Не важно", callback_data="user:createprofile:find_sex:any"),
            ]
        ]
    )


def media_done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Готово", callback_data="user:createprofile:media:done"
                )
            ]
        ]
    )


def publish_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыто (с фото)", callback_data="user:createprofile:publish:open"
                ),
                InlineKeyboardButton(
                    text="Анонимно", callback_data="user:createprofile:publish:anonymous"
                ),
            ]
        ]
    )


def anonymous_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить", pay=True
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад", callback_data="user:createprofile:publish:back"
                )
            ],
        ]
    )


def family_status_keyboard(sex: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Был в браке" if sex else "Была в браке",
                    callback_data="user:createprofile:family:married"
                ),
                InlineKeyboardButton(
                    text="Брака не было", callback_data="user:createprofile:family:nevermarried"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Есть дети", callback_data="user:createprofile:family:havechildren"
                ),
                InlineKeyboardButton(
                    text="Нет детей", callback_data="user:createprofile:family:havenochildren"
                ),
            ],
        ]
    )
