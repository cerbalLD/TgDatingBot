import os
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, FSInputFile, InputMediaPhoto, InputMediaVideo

async def _send_with_files(
    bot: Bot,
    user_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup = None,
    file_paths: list[str] = None,
    media_group: bool = False
    ):

    if file_paths:
        resolved_paths = []
        for path in file_paths:
            if not path:
                continue
            normalized = _normalize_file_path(path)
            if os.path.exists(normalized):
                resolved_paths.append(normalized)
        file_paths = resolved_paths

    if not file_paths:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )
        return
    
    # Отправка одиночного файла
    if len(file_paths) == 1:
        # Определяем тип файла по расширению
        file_methods = {
            'photo': bot.send_photo,
            'video': bot.send_video,
            'document': bot.send_document,
            'audio': bot.send_audio,
            'animation': bot.send_animation,
            'voice': bot.send_voice,
            'video_note': bot.send_video_note,
            'sticker': bot.send_sticker,
        }
        
        file_path = _normalize_file_path(file_paths[0])
        file_type = _get_file_type(file_path)
        
        if file_type in file_methods:
            input_file = FSInputFile(file_path)
            
            params = {
                'chat_id': user_id,
                'reply_markup': reply_markup,
            }
            
            if file_type in ['photo', 'video', 'animation'] and text:
                params['caption'] = text
            
            if file_type == 'photo':
                params['photo'] = input_file
            elif file_type == 'video':
                params['video'] = input_file
            elif file_type == 'document':
                params['document'] = input_file
            elif file_type == 'audio':
                params['audio'] = input_file
                if text:
                    params['title'] = text
            elif file_type == 'animation':
                params['animation'] = input_file
            elif file_type == 'voice':
                params['voice'] = input_file
            elif file_type == 'video_note':
                params['video_note'] = input_file
            elif file_type == 'sticker':
                params['sticker'] = input_file
            
            print(input_file)
            await file_methods[file_type](**params)
            
            if file_type not in ['photo', 'video', 'animation'] and text:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=reply_markup
                )
    
    # Отправка медиагруппы (только фото/видео)
    else:
        media = []
        for i, file_path in enumerate(file_paths):
            file_path = _normalize_file_path(file_path)
            file_type = _get_file_type(file_path)
            
            if file_type == 'photo':
                input_file = FSInputFile(file_path)
                media_item = InputMediaPhoto(
                    media=input_file,
                    caption=text if i == 0 and reply_markup == None else None
                )
                media.append(media_item)
            elif file_type == 'video':
                input_file = FSInputFile(file_path)
                media_item = InputMediaVideo(
                    media=input_file,
                    caption=text if i == 0 and reply_markup == None  else None
                )
                media.append(media_item)
            else:
                # Неподдерживаемые типы для медиагруппы отправляем отдельно
                await _send_single_file(
                    bot=bot,
                    user_id=user_id,
                    file_path=file_path,
                    file_type=file_type
                )
        
        if media:
            await bot.send_media_group(
                chat_id=user_id,
                media=media
            )
            
            # Отправляем клавиатуру отдельно
            if reply_markup:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=reply_markup
                )

async def _send_single_file(
    bot: Bot,
    user_id: int,
    file_path: str,
    file_type: str
):
    """Отправка одиночного файла"""
    file_path = _normalize_file_path(file_path)
    input_file = FSInputFile(file_path)
    
    if file_type == 'photo':
        await bot.send_photo(chat_id=user_id, photo=input_file)
    elif file_type == 'video':
        await bot.send_video(chat_id=user_id, video=input_file)
    elif file_type == 'document':
        await bot.send_document(chat_id=user_id, document=input_file)
    elif file_type == 'audio':
        await bot.send_audio(chat_id=user_id, audio=input_file)
    elif file_type == 'animation':
        await bot.send_animation(chat_id=user_id, animation=input_file)
            
def _get_file_type(file_path: str) -> str:
    """Определяет тип файла по расширению"""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Фото
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        # WEBP может быть стикером или фото
        if ext == '.webp' and 'sticker' in file_path.lower():
            return 'sticker'
        return 'photo'
    # Видео
    elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        return 'video'
    # Аудио
    elif ext in ['.mp3', '.ogg', '.wav', '.m4a', '.flac']:
        return 'audio'
    # Голосовые (обычно .ogg)
    elif ext == '.ogg' and 'voice' in file_path.lower():
        return 'voice'
    # Видеосообщения
    elif ext == '.mp4' and ('video_note' in file_path.lower() or 'round' in file_path.lower()):
        return 'video_note'
    # Стикеры
    elif ext == '.webp' or ext == '.tgs':
        return 'sticker'
    # GIF анимации
    elif ext == '.gif':
        return 'animation'
    # Остальное как документ
    else:
        return 'document'


def _normalize_file_path(file_path: str) -> str:
    if not file_path:
        return file_path
    normalized = os.path.normpath(file_path)
    if os.path.exists(normalized):
        return normalized
    if not os.path.isabs(normalized):
        base_path = os.environ.get("BASE_PATH")
        if base_path:
            base_path = os.path.normpath(base_path)
            abs_path = os.path.normpath(os.path.join(base_path, normalized))
            if os.path.exists(abs_path):
                return abs_path
    if "\\" in file_path:
        normalized = file_path.replace("\\", "/")
    return normalized
