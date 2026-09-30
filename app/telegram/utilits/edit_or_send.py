from aiogram.types import Message, InlineKeyboardMarkup
from .send import _send_with_files

async def edit_or_send(
        message: Message, 
        user_id: int, 
        text: str, 
        reply_markup: InlineKeyboardMarkup = None,
        file_paths: list[str] = None,
        media_group: bool = False
    ):
        """Редактирует сообщение или отправляет новое с поддержкой файлов"""
        try:
            if not file_paths:
                await message.edit_text(
                    text, 
                    reply_markup=reply_markup
                )
            else:
                await message.delete()
                await _send_with_files(
                    bot=message.bot,
                    user_id=user_id,
                    text=text,
                    reply_markup=reply_markup,
                    file_paths=file_paths,
                    media_group=media_group
                )
                
        except Exception:
            await _send_with_files(
                bot=message.bot,
                user_id=user_id,
                text=text,
                reply_markup=reply_markup,
                file_paths=file_paths,
                media_group=media_group
            )

    

    