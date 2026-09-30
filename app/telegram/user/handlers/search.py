from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from store import Store
from store.elastic import find_next_profile
from telegram.user.keyboards.search import limit_keyboard, search_keyboard
from telegram.utilits.send_profile import format_text
from telegram.utilits.anon_media import get_anonymous_media_path
from telegram.utilits.send import _send_with_files
from config import FREE_VIEW_LIMIT

router = Router()

FREE_VIEW_LIMIT_TOTAL = FREE_VIEW_LIMIT


def _has_active_subscription(user) -> bool:
    expires = user.expire_subscription_date
    return bool(expires and expires > datetime.utcnow())


def _utc_day_start() -> datetime:
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)



async def _build_contact_link(bot: Bot, user_id: int) -> str:
    try:
        chat = await bot.get_chat(user_id)
    except Exception:
        return f"tg://user?id={user_id}"

    if chat.username:
        return f"https://t.me/{chat.username}"
    return f"tg://user?id={user_id}"


async def _send_match_messages(bot: Bot, user_id: int, target_user_id: int) -> None:
    user_link = await _build_contact_link(bot, user_id)
    target_link = await _build_contact_link(bot, target_user_id)
    try:
        await bot.send_message(
            user_id,
            f"У вас мэтч! Можно знакомиться: {target_link}"
        )
    except Exception:
        pass
    try:
        await bot.send_message(
            target_user_id,
            f"У вас мэтч! Можно знакомиться: {user_link}"
        )
    except Exception:
        pass


async def _send_next_profile(callback: CallbackQuery):
    viewer_id = callback.from_user.id
    viewer = Store.user.get_by_user_id(viewer_id)
    if not viewer:
        await callback.message.answer("Профиль не найден.")
        return

    if not _has_active_subscription(viewer):
        viewed_total = Store.swipe.count_by_user_since(user_id=viewer_id, since=_utc_day_start())
        if viewed_total >= FREE_VIEW_LIMIT_TOTAL:
            await callback.message.answer(
                "Хочешь увидеть все анкеты и узнать, кто ставит тебе лайки?\nТогда приглашаем в нашу Премиум версию",
                reply_markup=limit_keyboard(),
            )
            return

    candidate = find_next_profile(viewer_id)
    if not candidate:
        await callback.message.answer(
            "Пока нет подходящих анкет рядом. Попробуйте позже."
        )
        return

    medias = Store.media.list(user_id=candidate.user_id)
    file_paths = [media.path for media in medias] if medias else []
    if candidate.is_anonymous and viewer_id != candidate.user_id:
        file_paths = [get_anonymous_media_path(candidate.sex)]
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_with_files(
        bot=callback.bot,
        user_id=viewer_id,
        text=format_text(candidate),
        reply_markup=search_keyboard(candidate.user_id),
        file_paths=file_paths,
    )


@router.callback_query(F.data == "user:main_menu:search")
async def cb_search(callback: CallbackQuery):
    await callback.answer()
    user = Store.user.get_by_user_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала создайте анкету.")
        return
    if not user.is_approved:
        await callback.message.answer(
            "Ваша анкета еще не прошла модерацию. Доступ к просмотру анкет откроется после одобрения."
        )
        return
    await _send_next_profile(callback)


@router.callback_query(F.data.startswith("user:search:like:"))
async def cb_like(callback: CallbackQuery):
    await callback.answer()
    viewer_id = callback.from_user.id
    viewer = Store.user.get_by_user_id(viewer_id)
    if not viewer:
        await _send_next_profile(callback)
        return

    target_user_id = int(callback.data.split(":")[-1])
    target = Store.user.get_by_user_id(target_user_id)
    if not target:
        await _send_next_profile(callback)
        return

    existing = Store.swipe.get_by_user_target_version(
        user_id=viewer_id,
        target_user_id=target_user_id,
        target_version=target.profile_version,
    )
    if existing:
        await _send_next_profile(callback)
        return

    Store.swipe.create(
        user_id=viewer_id,
        target_user_id=target_user_id,
        target_version=target.profile_version,
        action=1,
    )

    other_swipe = Store.swipe.get_by_user_target_version(
        user_id=target_user_id,
        target_user_id=viewer_id,
        target_version=viewer.profile_version,
    )
    if other_swipe and other_swipe.action == 1:
        await _send_match_messages(callback.bot, viewer_id, target_user_id)
    await _send_next_profile(callback)


@router.callback_query(F.data.startswith("user:search:dislike:"))
async def cb_dislike(callback: CallbackQuery):
    await callback.answer()
    target_user_id = int(callback.data.split(":")[-1])
    target = Store.user.get_by_user_id(target_user_id)
    if not target:
        await _send_next_profile(callback)
        return

    existing = Store.swipe.get_by_user_target_version(
        user_id=callback.from_user.id,
        target_user_id=target_user_id,
        target_version=target.profile_version,
    )
    if not existing:
        Store.swipe.create(
            user_id=callback.from_user.id,
            target_user_id=target_user_id,
            target_version=target.profile_version,
            action=0,
        )

    await _send_next_profile(callback)
