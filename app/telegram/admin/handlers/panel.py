from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from telegram.admin.keyboards.main_menu import get_admin_panel
from telegram.admin.states.admin import AdminManageStates, AdminBroadcastStates
from telegram.admin.handlers.moderation import send_next_profile, send_profiles_by_status
from config import LIST_ADMIN_USER_ID
from store import Store

router = Router()


def _is_super_admin(user_id: int) -> bool:
    if isinstance(LIST_ADMIN_USER_ID, list):
        if user_id in LIST_ADMIN_USER_ID:
            return True
    elif user_id == LIST_ADMIN_USER_ID:
        return True
    admins = Store.admin.list(user_id=user_id, limit=1)
    return bool(admins and admins[0].level == 0)


@router.message(Command("admin"))
async def admin_panel(message: Message):
    is_super = _is_super_admin(message.from_user.id)
    await message.answer(
        "Админ панель:",
        reply_markup=get_admin_panel(is_super),
    )


@router.callback_query(F.data == "admin:panel:profiles")
async def cb_panel_profiles(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Открываю модерацию анкет...")
    await send_next_profile(callback.bot, callback.from_user.id)


@router.callback_query(F.data == "admin:panel:profiles:approved")
async def cb_panel_approved_profiles(callback: CallbackQuery):
    await callback.answer()
    await send_profiles_by_status(callback.bot, callback.from_user.id, "approved")


@router.callback_query(F.data == "admin:panel:profiles:rejected")
async def cb_panel_rejected_profiles(callback: CallbackQuery):
    await callback.answer()
    await send_profiles_by_status(callback.bot, callback.from_user.id, "rejected")


@router.callback_query(F.data == "admin:panel:add_admin")
async def cb_panel_add_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if not _is_super_admin(callback.from_user.id):
        await callback.message.answer("Недостаточно прав.")
        return
    await state.set_state(AdminManageStates.waiting_add_contact)
    await callback.message.answer("Отправьте контакт пользователя для добавления администратора.")


@router.callback_query(F.data == "admin:panel:remove_admin")
async def cb_panel_remove_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if not _is_super_admin(callback.from_user.id):
        await callback.message.answer("Недостаточно прав.")
        return
    await state.set_state(AdminManageStates.waiting_remove_contact)
    await callback.message.answer("Отправьте контакт администратора для удаления.")

@router.callback_query(F.data == "admin:panel:create_thread")
async def cb_panel_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminBroadcastStates.waiting_message)
    await callback.message.answer("Отправьте сообщение для рассылки.")


@router.message(AdminBroadcastStates.waiting_message)
async def st_broadcast_message(message: Message, state: FSMContext):
    await state.clear()
    sent = 0
    failed = 0
    limit = 100
    offset = 0
    while True:
        users = Store.user.list(limit=limit, offset=offset)
        if not users:
            break
        for user in users:
            try:
                await message.bot.copy_message(
                    chat_id=user.user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                )
                sent += 1
            except Exception:
                failed += 1
        offset += limit
    await message.answer(f"Рассылка завершена\nОтправлено: {sent}\nНе отправлено (возможно эти аккаунты были удалены): {failed}.")
