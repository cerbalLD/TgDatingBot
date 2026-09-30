from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from store import Store
from telegram.admin.keyboards.moderation import (
    moderation_keyboard,
    reject_reason_keyboard,
    profile_status_confirm_keyboard,
    profile_status_review_keyboard,
)
from telegram.utilits.send_profile import format_text
from telegram.admin.states.admin import AdminModerationStates
from telegram.user.keyboards.main_menu import main_menu
from telegram.utilits.send import _send_with_files
from store.elastic import index_profile

router = Router()

MODERATION_PENDING = "pending"
MODERATION_APPROVED = "approved"
MODERATION_REJECTED = "rejected"

STATUS_TITLES = {
    MODERATION_APPROVED: "Одобренные анкеты",
    MODERATION_REJECTED: "Отклонённые анкеты",
}


def _profile_media_paths(user) -> list[str]:
    medias = Store.media.list(user_id=user.user_id, profile_version=user.profile_version)
    return [media.path for media in medias] if medias else []


def _admin_profile_text(user, title: str, position: int | None = None, total: int | None = None) -> str:
    lines = [title]
    if position is not None and total is not None:
        lines.append(f"Анкета {position} из {total}")
    lines.extend([
        f"User ID: {user.user_id}",
        format_text(user),
    ])
    return "\n".join(lines)


async def _send_profile_to_admin(bot, admin_id: int, user, text: str, reply_markup) -> None:
    await _send_with_files(
        bot=bot,
        user_id=admin_id,
        text=text,
        reply_markup=reply_markup,
        file_paths=_profile_media_paths(user),
    )


async def _notify_profile_approved(bot, user_id: int) -> None:
    try:
        await bot.send_message(
            chat_id=user_id,
            text="Ваша анкета одобрена.",
            reply_markup=main_menu(True, True),
        )
    except Exception:
        pass


async def send_next_profile(bot, admin_id: int) -> None:
    users = Store.user.list(limit=1, moderation_status=MODERATION_PENDING)
    if not users:
        await bot.send_message(
            chat_id=admin_id,
            text="Нет анкет на модерации.",
        )
        return

    user = users[0]
    await _send_profile_to_admin(
        bot,
        admin_id,
        user,
        _admin_profile_text(user, "Анкета на модерации"),
        moderation_keyboard(user.user_id),
    )


async def send_profiles_by_status(bot, admin_id: int, status: str, offset: int = 0) -> None:
    if status not in STATUS_TITLES:
        await bot.send_message(chat_id=admin_id, text="Неизвестный раздел анкет.")
        return

    total = Store.user.count(moderation_status=status)
    if total <= 0:
        await bot.send_message(chat_id=admin_id, text=f"{STATUS_TITLES[status]}: список пуст.")
        return

    offset = max(0, min(offset, total - 1))
    users = Store.user.list(limit=1, offset=offset, moderation_status=status)
    if not users:
        await bot.send_message(chat_id=admin_id, text=f"{STATUS_TITLES[status]}: список пуст.")
        return

    user = users[0]
    await _send_profile_to_admin(
        bot,
        admin_id,
        user,
        _admin_profile_text(user, STATUS_TITLES[status], offset + 1, total),
        profile_status_review_keyboard(
            status=status,
            user_id=user.user_id,
            offset=offset,
            total=total,
        ),
    )


@router.message(Command("moderate"))
async def cmd_moderate(message: Message):
    await send_next_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "admin:moderation:next")
async def cb_next_profile(callback: CallbackQuery):
    await callback.answer()
    await send_next_profile(callback.bot, callback.from_user.id)


@router.callback_query(F.data.startswith("admin:moderation:approve:"))
async def cb_approve_profile(callback: CallbackQuery):
    await callback.answer()
    user_id = int(callback.data.split(":")[-1])
    user = Store.user.get_by_user_id(user_id)
    if not user:
        await callback.message.answer("Анкета не найдена")
        return

    Store.user.update(user.id, is_approved=True, moderation_status=MODERATION_APPROVED)
    updated = Store.user.get_by_user_id(user_id)
    if updated:
        index_profile(updated)
    await _notify_profile_approved(callback.bot, user_id)



@router.callback_query(F.data.startswith("admin:moderation:reject:"))
async def cb_reject_profile(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = int(callback.data.split(":")[-1])
    user = Store.user.get_by_user_id(user_id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return

    Store.user.update(user.id, is_approved=False, moderation_status=MODERATION_REJECTED)
    updated = Store.user.get_by_user_id(user_id)
    if updated:
        index_profile(updated)
    await state.set_state(AdminModerationStates.waiting_reject_reason)
    await state.update_data(reject_user_id=user_id)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "Напишите причину отказа или нажмите кнопку чтобы пропустить",
        reply_markup=reject_reason_keyboard(),
    )


@router.callback_query(F.data == "admin:moderation:reject_reason:skip")
async def cb_reject_reason_skip(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    if user_id:
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text="Действие отменено",
            )
        except Exception:
            pass
    await state.clear()
    await send_next_profile(callback.bot, callback.from_user.id)


@router.message(AdminModerationStates.waiting_reject_reason)
async def st_reject_reason(message: Message, state: FSMContext):
    reason = (message.text or "").strip()
    if not reason:
        await message.answer("Напишите причину отказа или нажмите кнопку чтобы пропустить", reply_markup=reject_reason_keyboard())
        return
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    if user_id:
        try:
            await message.bot.send_message(chat_id=user_id, text=reason)
        except Exception:
            pass
    await state.clear()
    await send_next_profile(message.bot, message.from_user.id)


@router.callback_query(F.data.startswith("admin:profiles:list:"))
async def cb_profiles_list(callback: CallbackQuery):
    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) != 5:
        return
    status = parts[3]
    try:
        offset = int(parts[4])
    except ValueError:
        offset = 0
    await send_profiles_by_status(callback.bot, callback.from_user.id, status, offset)


@router.callback_query(F.data.startswith("admin:profiles:ask:"))
async def cb_profile_status_ask(callback: CallbackQuery):
    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) != 6:
        return
    action = parts[3]
    try:
        user_id = int(parts[4])
        offset = int(parts[5])
    except ValueError:
        return

    user = Store.user.get_by_user_id(user_id)
    if not user:
        await callback.message.answer("Анкета не найдена")
        return

    if action == "reject":
        current_status = MODERATION_APPROVED
        question = "Вы уверены, что хотите отклонить эту анкету?"
    elif action == "approve":
        current_status = MODERATION_REJECTED
        question = "Вы уверены, что хотите одобрить эту анкету?"
    else:
        return

    if user.moderation_status != current_status:
        await callback.message.answer("Статус анкеты уже изменился.")
        await send_profiles_by_status(callback.bot, callback.from_user.id, current_status, offset)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        question,
        reply_markup=profile_status_confirm_keyboard(
            action=action,
            user_id=user_id,
            current_status=current_status,
            offset=offset,
        ),
    )


@router.callback_query(F.data.startswith("admin:profiles:do:"))
async def cb_profile_status_do(callback: CallbackQuery):
    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) != 6:
        return
    action = parts[3]
    try:
        user_id = int(parts[4])
        offset = int(parts[5])
    except ValueError:
        return

    user = Store.user.get_by_user_id(user_id)
    if not user:
        await callback.message.answer("Анкета не найдена")
        return

    if action == "reject":
        expected_status = MODERATION_APPROVED
        target_status = MODERATION_REJECTED
        approved = False
        result_text = "Анкета отклонена."
    elif action == "approve":
        expected_status = MODERATION_REJECTED
        target_status = MODERATION_APPROVED
        approved = True
        result_text = "Анкета одобрена."
    else:
        return

    if user.moderation_status != expected_status:
        await callback.message.answer("Статус анкеты уже изменился.")
        await send_profiles_by_status(callback.bot, callback.from_user.id, expected_status, offset)
        return

    Store.user.update(user.id, is_approved=approved, moderation_status=target_status)
    updated = Store.user.get_by_user_id(user_id)
    if updated:
        index_profile(updated)
    if action == "approve":
        await _notify_profile_approved(callback.bot, user_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(result_text)
    await send_profiles_by_status(callback.bot, callback.from_user.id, target_status, 0)
