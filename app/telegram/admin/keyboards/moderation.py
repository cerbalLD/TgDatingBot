from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def moderation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Одобрить", callback_data=f"admin:moderation:approve:{user_id}"
                ),
                InlineKeyboardButton(
                    text="Отклонить", callback_data=f"admin:moderation:reject:{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Далее", callback_data="admin:moderation:next"
                )
            ],
        ]
    )


def reject_reason_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Не надо", callback_data="admin:moderation:reject_reason:skip"
                )
            ]
        ]
    )


def profile_status_review_keyboard(
    *,
    status: str,
    user_id: int,
    offset: int,
    total: int,
) -> InlineKeyboardMarkup:
    prev_offset = max(offset - 1, 0)
    next_offset = min(offset + 1, max(total - 1, 0))

    action_text = "Отклонить анкету" if status == "approved" else "Одобрить анкету"
    action = "reject" if status == "approved" else "approve"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"admin:profiles:list:{status}:{prev_offset}",
                ),
                InlineKeyboardButton(
                    text="➡️ Вперёд",
                    callback_data=f"admin:profiles:list:{status}:{next_offset}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=action_text,
                    callback_data=f"admin:profiles:ask:{action}:{user_id}:{offset}",
                )
            ],
        ]
    )


def profile_status_confirm_keyboard(
    *,
    action: str,
    user_id: int,
    current_status: str,
    offset: int,
) -> InlineKeyboardMarkup:
    confirm_text = "Да, отклонить" if action == "reject" else "Да, одобрить"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=confirm_text,
                    callback_data=f"admin:profiles:do:{action}:{user_id}:{offset}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=f"admin:profiles:list:{current_status}:{offset}",
                )
            ],
        ]
    )
