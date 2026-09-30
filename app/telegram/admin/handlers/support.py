from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from store import Store
from telegram.utilits.send_profile import format_text
from telegram.utilits.send import _send_with_files
from telegram.admin.keyboards.complaints import (
    profile_complaint_keyboard,
    complaint_ban_skip_keyboard,
)
from telegram.admin.states.admin import AdminComplaintStates
from store.elastic import index_profile

router = Router()


async def send_next_complaint(bot: Bot, admin_id: int) -> None:
    complaints = Store.complaint.list(limit=1, status=0, complaint_type=0)
    if not complaints:
        await bot.send_message(chat_id=admin_id, text="Список жалоб пуст")
        return

    complaint = complaints[0]
    forwarded = await bot.forward_message(
        chat_id=admin_id,
        from_chat_id=complaint.user_id,
        message_id=complaint.user_message_id,
    )

    Store.complaint.update(
        complaint.id,
        admin_id=admin_id,
        admin_message_id=forwarded.message_id,
        status=1,
    )

    await bot.send_message(
        chat_id=admin_id,
        text=f"жалоба #{complaint.id}\nОтвете на сообщение выше и ответ будет отправлен пользователю",
    )


async def send_next_profile_complaint(bot: Bot, admin_id: int) -> None:
    complaints = Store.complaint.list(limit=1, status=0, complaint_type=1)
    if not complaints:
        await bot.send_message(chat_id=admin_id, text="Список жалоб на профиль пуст")
        return

    complaint = complaints[0]
    forwarded = await bot.forward_message(
        chat_id=admin_id,
        from_chat_id=complaint.user_id,
        message_id=complaint.user_message_id,
    )

    Store.complaint.update(
        complaint.id,
        admin_id=admin_id,
        admin_message_id=forwarded.message_id,
        status=1,
    )

    target = Store.user.get_by_user_id(complaint.target_user_id) if complaint.target_user_id else None
    if not target:
        await bot.send_message(chat_id=admin_id, text="Пользователь на которого была жалоба удален")
        return

    medias = Store.media.list(user_id=target.user_id)
    file_paths = [media.path for media in medias] if medias else []
    await _send_with_files(
        bot=bot,
        user_id=admin_id,
        text=format_text(target),
        file_paths=file_paths,
    )
    await bot.send_message(
        chat_id=admin_id,
        text="Что делать?",
        reply_markup=profile_complaint_keyboard(complaint.id),
    )


@router.message(Command("support"))
async def cmd_support(message: Message):
    await send_next_complaint(message.bot, message.from_user.id)


@router.callback_query(F.data == "admin:panel:support")
async def cb_panel_support(callback: CallbackQuery):
    await callback.answer()
    await send_next_complaint(callback.bot, callback.from_user.id)


@router.callback_query(F.data == "admin:panel:complaints")
async def cb_panel_profile_complaints(callback: CallbackQuery):
    await callback.answer()
    await send_next_profile_complaint(callback.bot, callback.from_user.id)


@router.message(F.reply_to_message)
async def st_admin_reply(message: Message):
    complaint = Store.complaint.get_by_admin_message_id(message.reply_to_message.message_id)
    if not complaint or complaint.status != 1 or complaint.complaint_type != 0:
        return

    await message.bot.send_message(
        chat_id=complaint.user_id,
        text=f"Ответ администратора на жалобу #{complaint.id}",
    )
    await message.bot.copy_message(
        chat_id=complaint.user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    Store.complaint.update(complaint.id, status=2)
    await message.answer("Ответ отправлен")


@router.callback_query(F.data.startswith("admin:complaint:ban:"))
async def cb_complaint_ban(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        complaint_id = int(callback.data.split(":")[-1])
    except ValueError:
        return
    complaint = Store.complaint.get(complaint_id)
    if not complaint or complaint.complaint_type != 1:
        return
    target = Store.user.get_by_user_id(complaint.target_user_id)
    if not target:
        await callback.message.answer("Пользователь на которого была жалоба удален")
        return

    Store.user.update(target.id, is_enabled=False, is_approved=False, moderation_status="rejected")
    updated = Store.user.get_by_user_id(target.user_id)
    if updated:
        index_profile(updated)

    await state.set_state(AdminComplaintStates.waiting_ban_message)
    await state.update_data(complaint_id=complaint.id, target_user_id=target.user_id)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "Напишите сообщение которое будет отправлено пользователю",
        reply_markup=complaint_ban_skip_keyboard(),
    )


@router.callback_query(F.data.startswith("admin:complaint:skip:"))
async def cb_complaint_skip(callback: CallbackQuery):
    await callback.answer()
    try:
        complaint_id = int(callback.data.split(":")[-1])
    except ValueError:
        return
    complaint = Store.complaint.get(complaint_id)
    if not complaint or complaint.complaint_type != 1:
        return
    Store.complaint.update(complaint_id, status=2)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer("Вопрос закрыт")


@router.callback_query(F.data == "admin:complaint:ban:skip")
async def cb_complaint_ban_skip(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    complaint_id = data.get("complaint_id")
    if complaint_id:
        Store.complaint.update(complaint_id, status=2)
    await state.clear()
    await callback.message.answer("Вопрос закрыт")


@router.message(AdminComplaintStates.waiting_ban_message)
async def st_complaint_ban_message(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    complaint_id = data.get("complaint_id")
    if target_user_id and message.text:
        try:
            await message.bot.send_message(chat_id=target_user_id, text=message.text)
        except Exception:
            pass
    if complaint_id:
        Store.complaint.update(complaint_id, status=2)
    await state.clear()
    await message.answer("Вопрос закрыт")
