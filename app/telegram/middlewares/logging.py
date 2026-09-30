from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

import config


class UserActionLoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        action = None

        if isinstance(event, Message):
            action = event.text or event.caption or event.content_type
        elif isinstance(event, CallbackQuery):
            action = event.data

        config.logger.info(f"[user_action] user_id={user_id} action={action}")
        return await handler(event, data)
