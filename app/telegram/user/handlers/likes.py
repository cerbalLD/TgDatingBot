from aiogram import Router, F
from aiogram.types import CallbackQuery

from store import Store
from telegram.user.keyboards.likes import likes_queue_keyboard
from telegram.user.handlers.search import _send_match_messages
from telegram.utilits.send_profile import format_text
from telegram.utilits.anon_media import get_anonymous_media_path
from telegram.utilits.send import _send_with_files

router = Router()


def _is_valid_incoming_like(viewer, swipe) -> bool:
    if swipe.user_id == viewer.user_id:
        return False
    if swipe.target_version != viewer.profile_version:
        return False
    return True


async def _send_next_like(callback: CallbackQuery) -> None:
    viewer_id = callback.from_user.id
    viewer = Store.user.get_by_user_id(viewer_id)
    if not viewer:
        await callback.message.answer("Профиль не найден.")
        return

    incoming_swipes = Store.swipe.list_incoming_likes(user_id=viewer_id, limit=50, offset=0)
    for swipe in incoming_swipes:
        if not _is_valid_incoming_like(viewer, swipe):
            continue

        liker = Store.user.get_by_user_id(swipe.user_id)
        if not liker or not liker.is_approved or not liker.is_enabled:
            continue

        existing = Store.swipe.get_by_user_target_version(
            user_id=viewer_id,
            target_user_id=liker.user_id,
            target_version=liker.profile_version,
        )
        if existing:
            continue

        medias = Store.media.list(user_id=liker.user_id)
        file_paths = [media.path for media in medias] if medias else []
        if liker.is_anonymous and viewer_id != liker.user_id:
            file_paths = [get_anonymous_media_path(liker.sex)]

        try:
            await callback.message.delete()
        except Exception:
            pass

        await _send_with_files(
            bot=callback.bot,
            user_id=viewer_id,
            text=format_text(liker),
            reply_markup=likes_queue_keyboard(liker.user_id),
            file_paths=file_paths,
        )
        return

    await callback.message.answer("Пока нет новых лайков.")


@router.callback_query(F.data == "user:main_menu:matches")
async def cb_matches(callback: CallbackQuery):
    await callback.answer()
    await _send_next_like(callback)


@router.callback_query(F.data.startswith("user:likes:like:"))
async def cb_like_from_likes(callback: CallbackQuery):
    await callback.answer()
    viewer_id = callback.from_user.id
    viewer = Store.user.get_by_user_id(viewer_id)
    if not viewer:
        await _send_next_like(callback)
        return

    try:
        target_user_id = int(callback.data.split(":")[-1])
    except ValueError:
        await _send_next_like(callback)
        return

    target = Store.user.get_by_user_id(target_user_id)
    if not target:
        await _send_next_like(callback)
        return

    existing = Store.swipe.get_by_user_target_version(
        user_id=viewer_id,
        target_user_id=target_user_id,
        target_version=target.profile_version,
    )
    if not existing:
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

    await _send_next_like(callback)


@router.callback_query(F.data.startswith("user:likes:dislike:"))
async def cb_dislike_from_likes(callback: CallbackQuery):
    await callback.answer()
    viewer_id = callback.from_user.id
    viewer = Store.user.get_by_user_id(viewer_id)
    if not viewer:
        await _send_next_like(callback)
        return

    try:
        target_user_id = int(callback.data.split(":")[-1])
    except ValueError:
        await _send_next_like(callback)
        return

    target = Store.user.get_by_user_id(target_user_id)
    if not target:
        await _send_next_like(callback)
        return

    existing = Store.swipe.get_by_user_target_version(
        user_id=viewer_id,
        target_user_id=target_user_id,
        target_version=target.profile_version,
    )
    if not existing:
        Store.swipe.create(
            user_id=viewer_id,
            target_user_id=target_user_id,
            target_version=target.profile_version,
            action=0,
        )

    await _send_next_like(callback)
