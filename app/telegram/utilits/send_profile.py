from aiogram import Bot as Aiobot
from aiogram.types import InlineKeyboardMarkup
from store import Store, UsersTable
from .send import _send_with_files

async def send_profile(
        bot: Aiobot,
        user_id: int,
        reply_markup: InlineKeyboardMarkup = None,
    ):
    """Для отправки профиля"""
    user = Store.user.get_by_user_id(user_id)
    
    if not user:
        raise Exception("[send_profile] Пользователь не найден")
    
    text = format_text(user)
    medias = Store.media.list(user_id=user_id, profile_version=user.profile_version)
    file_paths = [media.path for media in medias] if medias else []

    await _send_with_files(
        bot=bot,
        user_id=user_id,
        text=text,
        reply_markup=reply_markup,
        file_paths=file_paths
    )
    
def format_text(user: UsersTable):
    """Форматирование текста профиля"""
    if user.is_anonymous:
        title = "Мистер" if user.sex else "Мисc"
        return "\n".join([
            f"{title} X, {user.name}, {user.age} лет",
            f"{user.text}"
        ])
    return "\n".join([
        f"{user.name}, {user.age} лет",
        f"📍 {user.city}",
        f"{user.text}"
    ])
