from aiogram.filters import Filter
from aiogram import types
from config import LIST_ADMIN_USER_ID
from store import Store


def _admin_ids() -> list[int]:
    if isinstance(LIST_ADMIN_USER_ID, list):
        return [int(user_id) for user_id in LIST_ADMIN_USER_ID]
    return [int(LIST_ADMIN_USER_ID)]

class IsAdmin(Filter):
    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return user_id in _admin_ids() + [admin.user_id for admin in Store.admin.list()]

class IsSuperAdmin(Filter):
    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        if user_id in _admin_ids():
            return True
        admins = Store.admin.list(user_id=user_id, limit=1)
        return bool(admins and admins[0].level == 0)
