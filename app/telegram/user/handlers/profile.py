import os
import uuid
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from telegram.user.keyboards.main_menu import main_menu
from telegram.user.keyboards.profile import (
    sex_keyboard,
    media_done_keyboard,
    publish_type_keyboard,
    family_status_keyboard,
)
from telegram.user.keyboards.profile_menu import profile_menu, profile_edit_menu
from telegram.user.filters.profile_states import InAnyProfileState
from telegram.user.states.profile import ProfileStates

from config import DOWNLOADS_PATH, ANONYMOUS_PROFILE_PRICE
from robokassa.service import create_anonymous_profile_payment, robokassa_ready
from utilits.city import resolve_city
from store import Store
from telegram.utilits.send_profile import format_text, send_profile
from store.elastic import index_profile
from telegram.utilits.edit_or_send import edit_or_send

router = Router()


def _anonymous_payment_keyboard(url: str, invoice_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить в Robokassa", url=url)],
            [InlineKeyboardButton(text="Проверить оплату", callback_data=f"user:createprofile:anonymous:check:{invoice_id}")],
            [InlineKeyboardButton(text="Назад", callback_data="user:createprofile:publish:back")],
        ]
    )

def _sex_value(value: str) -> bool:
    return value == "male"

def _parse_age(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None

async def _download_media(bot, user_id: int, file_id: str) -> str:
    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
    file = await bot.get_file(file_id)
    unique = uuid.uuid4().hex
    filename = f"{user_id}_{unique}_{os.path.basename(file.file_path)}"
    file_path = os.path.join(DOWNLOADS_PATH, filename)
    await bot.download_file(file.file_path, destination=file_path)
    return file_path


PROFILE_TEXT_LABELS = {
    "about": "Сфера деятельности",
    "activity": "Увлечения и хобби",
    "partner": "Какого партнера хочеться встретить",
    "family": "Семейное положение",
}


def _build_profile_text(about: str, activity: str, partner: str, family: str) -> str:
    return "\n\n".join([
        f"Сфера деятельности: {about}",
        f"Увлечения и хобби: {activity}",
        f"Какого партнера хочеться встретить: {partner}",
        f"Семейное положение: {family}",
    ])


def _parse_profile_text(text: str | None) -> dict[str, str]:
    result = {key: "" for key in PROFILE_TEXT_LABELS}
    if not text:
        return result
    parts = [part.strip() for part in text.split("\n\n") if part.strip()]
    for part in parts:
        for key, prefix in PROFILE_TEXT_LABELS.items():
            if part.startswith(prefix):
                _, _, value = part.partition(":")
                result[key] = value.strip()
                break
    return result


def _next_profile_version(user) -> int:
    return (user.profile_version or 1) + 1


def _update_media_version(user_id: int, profile_version: int) -> None:
    for media in Store.media.list(user_id=user_id):
        Store.media.update(media.id, profile_version=profile_version)


def _update_profile(user_id: int, *, update_media: bool = True, **fields):
    user = Store.user.get_by_user_id(user_id)
    if not user:
        return None
    new_version = _next_profile_version(user)
    Store.user.update(
        user.id,
        profile_version=new_version,
        is_approved=False,
        moderation_status="pending",
        **fields,
    )
    updated = Store.user.get_by_user_id(user_id)
    if updated and update_media:
        _update_media_version(user_id, updated.profile_version)
    return updated


async def _finalize_profile_edit(update: Message, state: FSMContext, user_id: int, updated) -> None:
    await state.clear()
    if updated:
        index_profile(updated)
    await _send_my_profile(update, user_id)
    await update.bot.send_message(
        chat_id=user_id,
        text="Анкета отправлена на модерацию. Мы напишем, когда будет результат.",
    )


async def _start_edit_flow(
    callback: CallbackQuery,
    state: FSMContext,
    field: str,
    next_state,
    prompt: str,
    reply_markup=None,
    extra_data: dict | None = None,
):
    await state.clear()
    await state.set_state(next_state)
    data = {"edit_mode": True, "edit_field": field}
    if extra_data:
        data.update(extra_data)
    await state.update_data(**data)
    await edit_or_send(
        message=callback.message,
        user_id=callback.from_user.id,
        text=prompt,
        reply_markup=reply_markup,
    )

async def _finalize_profile(update: Message, state: FSMContext, user_id: int):
    data = await state.get_data()

    name = data.get("name")
    age = _parse_age(str(data.get("age", "")).strip())
    city = data.get("city")
    about = data.get("about")
    activity = data.get("activity")
    partner = data.get("partner")
    family = data.get("family")
    text = _build_profile_text(about, activity, partner, family)

    sex = data.get("sex")

    if age is None:
        await update.answer("Возраст должен быть числом.")
        await state.set_state(ProfileStates.waiting_age)
        return

    existing = Store.user.get_by_user_id(user_id)
    is_anonymous = bool(data.get("is_anonymous"))
    if existing:
        Store.user.update(
            existing.id,
            name=name,
            age=age,
            city=city,
            sex=sex,
            text=text,
            is_anonymous=is_anonymous,
            is_approved=False,
            moderation_status="pending",
            is_enabled=True,
            profile_version=(existing.profile_version or 1) + 1,
        )
        updated = Store.user.get_by_user_id(user_id)
    else:
        Store.user.create(
            user_id=user_id,
            name=name,
            age=age,
            city=city,
            sex=sex,
            text=text,
            is_anonymous=is_anonymous,
            is_approved=False,
            moderation_status="pending",
            is_enabled=True,
            profile_version=1,
            expire_subscription_date=datetime.utcnow(),
        )
        updated = Store.user.get_by_user_id(user_id)

    media_ids = data.get("medias", [])
    for file_id in media_ids:
        media_path = await _download_media(update.bot, user_id, file_id)
        Store.media.create(user_id=user_id, path=media_path, profile_version=updated.profile_version)
    
    if updated.profile_version > 1:
        for old_file in Store.media.list(user_id=user_id, profile_version=updated.profile_version - 1):
            os.remove(old_file.path)
            Store.media.delete(old_file.id)

    if updated:
        index_profile(updated)


    await state.clear()
    await send_profile(update.bot, user_id, reply_markup=main_menu(True, True))
    await update.bot.send_message(
        chat_id=user_id,
        text="Анкета отправлена на модерацию. Мы напишем, когда будет результат.",
    )

async def _send_my_profile(message: Message, user_id: int):
    user = Store.user.get_by_user_id(user_id)
    if not user:
        return
    medias = Store.media.list(user_id=user_id, profile_version=user.profile_version)
    text = format_text(user)
    await edit_or_send(
        message=message,
        user_id=user_id,
        text=text,
        reply_markup=profile_menu(user.is_enabled),
        file_paths=[media.path for media in medias],
    )

@router.callback_query(F.data == "user:main_menu:myprofile")
async def cb_myprofile(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    user = Store.user.get_by_user_id(user_id)
    if not user:
        await cb_createprofile(callback, state)
        return
        
    await _send_my_profile(callback.message, user_id)


@router.callback_query(F.data == "user:profile_menu:back")
async def cb_profile_back(callback: CallbackQuery):
    await callback.answer()
    user = Store.user.get_by_user_id(callback.from_user.id)
    await edit_or_send(
        message=callback.message,
        user_id=callback.from_user.id,
        text="Главное меню",
        reply_markup=main_menu(user is not None, user.is_enabled if user else True),
    )


@router.callback_query(F.data == "user:profile_menu:edit")
async def cb_profile_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user = Store.user.get_by_user_id(callback.from_user.id)
    if not user:
        await cb_createprofile(callback, state)
        return
    await edit_or_send(
        message=callback.message,
        user_id=callback.from_user.id,
        text="Что хотите изменить?",
        reply_markup=profile_edit_menu(),
    )


@router.callback_query(F.data.startswith("user:profile_edit:"))
async def cb_profile_edit_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    user = Store.user.get_by_user_id(user_id)
    if not user:
        await cb_createprofile(callback, state)
        return

    if action == "back":
        await _send_my_profile(callback.message, user_id)
        return
    if action == "reset":
        await cb_createprofile(callback, state)
        return
    if action == "photo":
        await _start_edit_flow(
            callback,
            state,
            field="photo",
            next_state=ProfileStates.waiting_photo,
            prompt="Отправьте новые фото. После загрузки нажмите «Готово».",
            reply_markup=media_done_keyboard(),
            extra_data={"medias": []},
        )
        return
    if action == "name":
        await _start_edit_flow(
            callback,
            state,
            field="name",
            next_state=ProfileStates.waiting_name,
            prompt="Как тебя зовут?",
        )
        return
    if action == "age":
        await _start_edit_flow(
            callback,
            state,
            field="age",
            next_state=ProfileStates.waiting_age,
            prompt="Сколько тебе лет?",
        )
        return
    if action == "sex":
        await _start_edit_flow(
            callback,
            state,
            field="sex",
            next_state=ProfileStates.waiting_sex,
            prompt="Укажи свой пол",
            reply_markup=sex_keyboard("sex"),
        )
        return
    if action == "city":
        await _start_edit_flow(
            callback,
            state,
            field="city",
            next_state=ProfileStates.waiting_city,
            prompt="В каком городе хочешь встретить любовь?",
        )
        return
    if action == "q1":
        await _start_edit_flow(
            callback,
            state,
            field="about",
            next_state=ProfileStates.waiting_about,
            prompt="Расскажи о себе: какая у тебя сфера деятельности?",
        )
        return
    if action == "q2":
        await _start_edit_flow(
            callback,
            state,
            field="activity",
            next_state=ProfileStates.waiting_activity,
            prompt="Твои увлечения и хобби: как любишь проводить свободное время?",
        )
        return
    if action == "q3":
        await _start_edit_flow(
            callback,
            state,
            field="partner",
            next_state=ProfileStates.waiting_partner,
            prompt="Какого партнера видите рядом с собой? Опиши, что важно.",
        )
        return
    if action == "q4":
        await _start_edit_flow(
            callback,
            state,
            field="family",
            next_state=ProfileStates.waiting_family,
            prompt="Семейное положение:",
            reply_markup=family_status_keyboard(sex=user.sex),
        )
        return
@router.callback_query(F.data == "user:profile_menu:disable")
async def cb_profile_disable(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user = Store.user.get_by_user_id(user_id)
    if not user:
        return

    new_status = not user.is_enabled
    Store.user.update(user.id, is_enabled=new_status)
    updated = Store.user.get_by_user_id(user_id)
    if updated:
        index_profile(updated)

    await _send_my_profile(callback.message, user_id)

    
@router.callback_query(F.data == "user:main_menu:createprofile")
async def cb_createprofile(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileStates.waiting_sex)
    await edit_or_send(
        message=callback.message,
        user_id=callback.from_user.id,
        text="Укажи свой пол",
        reply_markup=sex_keyboard("sex"),
    )
    


@router.callback_query(F.data == "user:main_menu:disableprofile")
async def cb_disableprofile(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = Store.user.get_by_user_id(user_id)
    if not user:
        await cb_createprofile(callback, state)
        return

    new_status = not user.is_enabled
    Store.user.update(user.id, is_enabled=new_status)
    updated = Store.user.get_by_user_id(user_id)
    if updated:
        index_profile(updated)

    text = "Анкета включена." if new_status else "Анкета выключена и больше не будет показана другим пока вы не включите ее."
    await edit_or_send(
        message=callback.message,
        user_id=user_id,
        text=text,
        reply_markup=main_menu(True, new_status),
    )


@router.message(InAnyProfileState())
@router.callback_query(
    F.data.startswith("user:createprofile:sex:") |
    F.data.startswith("user:createprofile:publish:") |
    F.data.startswith("user:createprofile:family:") |
    (F.data == "user:createprofile:media:done") |
    F.data.startswith("user:createprofile:anonymous:check:")
)
async def st_profile_states(update: Message | CallbackQuery, state: FSMContext):
    if isinstance(update, CallbackQuery):
        current_state = await state.get_state()
        data = await state.get_data()
        value = update.data.split(":")[-1]
        await update.answer()

        if update.data.startswith("user:createprofile:anonymous:check:"):
            try:
                invoice_id = int(update.data.split(":")[-1])
            except ValueError:
                await update.message.answer("Некорректный номер платежа")
                return

            payment = Store.payment.get_by_invoice_id(invoice_id)
            if not payment or payment.user_id != update.from_user.id or payment.payment_type != "anonymous_profile":
                await update.message.answer("Платеж не найден")
                return

            if payment.status != 1:
                await update.message.answer(
                    "Платеж еще не подтвержден. Если вы оплатили только что, подождите 10-30 секунд и проверьте снова."
                )
                return

            if not payment.is_applied:
                Store.payment.update(payment.id, is_applied=True)

            await state.update_data(is_anonymous=True, anonymous_verification=True)
            await state.set_state(ProfileStates.waiting_photo)
            await update.message.answer("Оплата подтверждена.")
            await update.message.answer("Пришлите фото для верификации.")
            return

        if current_state == ProfileStates.waiting_sex.state:
            if data.get("edit_mode") and data.get("edit_field") == "sex":
                updated = _update_profile(update.from_user.id, sex=_sex_value(value))
                await _finalize_profile_edit(update.message, state, update.from_user.id, updated)
                return
            await state.update_data(sex=_sex_value(value))
            await state.set_state(ProfileStates.waiting_name)
            await update.message.delete()
            photo = FSInputFile("./assets/whats_you_name.PNG")
            await update.bot.send_photo(
                chat_id=update.from_user.id,
                photo=photo,
                caption="Как тебя зовут?",
            )
            return

        if current_state == ProfileStates.waiting_family.state:
            family_type = {
                "nevermarried": "Брака не было",
                "never_married": "Брака не было",
                "havechildren": "Есть дети",
                "havenochildren": "Нет детей",
            }
            if data.get("edit_mode") and data.get("edit_field") == "family":
                user = Store.user.get_by_user_id(update.from_user.id)
                if not user:
                    await state.clear()
                    return
                value = ("Был в браке" if user.sex else "Была в браке") if value == "married" else family_type.get(value, value)
                answers = _parse_profile_text(user.text)
                answers["family"] = value
                new_text = _build_profile_text(
                    answers["about"], answers["activity"], answers["partner"], answers["family"]
                )
                updated = _update_profile(update.from_user.id, text=new_text)
                await _finalize_profile_edit(update.message, state, update.from_user.id, updated)
                return
            data = await state.get_data()
            value = ("Был в браке" if data.get("sex") else "Была в браке") if value == "married" else family_type.get(value, value)
            await state.update_data(family=value)
            await state.set_state(ProfileStates.waiting_publish)
            photo = FSInputFile("./assets/is_anon.PNG")
            await update.bot.send_photo(
                chat_id=update.from_user.id,
                photo=photo,
                caption="\n".join([
                    "<b>Как хочешь опубликовать свою анкету: </b>",
                    "",
                    "открыто (с фото и именем) или анонимно (без фото и имени)?",
                ]),
                parse_mode="HTML",
                reply_markup=publish_type_keyboard(),
                )
            return
        if current_state == ProfileStates.waiting_photo.state and update.data == "user:createprofile:media:done":
            media_ids = data.get("medias", [])
            if not media_ids:
                await update.answer("Нужно добавить хотя бы одно фото или видео.")
                return
            if update.message:
                try:
                    await update.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            if data.get("edit_mode") and data.get("edit_field") == "photo":
                user_id = update.from_user.id
                old_media = Store.media.list(user_id=user_id)
                updated = _update_profile(user_id, update_media=False)
                if not updated:
                    await state.clear()
                    return
                for file_id in media_ids:
                    media_path = await _download_media(update.bot, user_id, file_id)
                    Store.media.create(user_id=user_id, path=media_path, profile_version=updated.profile_version)
                for old_file in old_media:
                    try:
                        os.remove(old_file.path)
                    except Exception:
                        pass
                    Store.media.delete(old_file.id)
                await _finalize_profile_edit(update.message, state, user_id, updated)
                return
            await _finalize_profile(update.message or update, state, update.from_user.id)
            return

        if current_state == ProfileStates.waiting_publish.state:
            if value == "back":
                await state.update_data(is_anonymous=None, anonymous_verification=False)
                if update.message:
                    try:
                        await update.message.edit_reply_markup(reply_markup=None)
                    except Exception:
                        pass
                    await update.message.answer(
                        "\n".join([
                            "<b>Как хочешь опубликовать свою анкету: </b>",
                            "",
                            "открыто (с фото и именем) или анонимно (без фото и имени)?",
                        ]),
                        reply_markup=publish_type_keyboard(),
                        parse_mode="HTML"
                    )
                else:
                    await update.bot.send_message(
                        chat_id=update.from_user.id,
                        text="\n".join([
                            "<b>Как хочешь опубликовать свою анкету: </b>",
                            "",
                            "открыто (с фото и именем) или анонимно (без фото и имени)?",
                        ]),
                        reply_markup=publish_type_keyboard(),
                        parse_mode="HTML"
                    )
                return
            is_anonymous = value == "anonymous"
            await state.update_data(is_anonymous=is_anonymous)
            if update.message:
                try:
                    await update.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            if not is_anonymous:
                await state.set_state(ProfileStates.waiting_photo)
                if update.message:
                    await update.message.answer(
                        "Отлично❤️ Загрузи 3 фотографии в хорошем качестве, где хорошо видно твое лицо. По желанию можно добавить 1 видео",
                        reply_markup=media_done_keyboard(),
                    )
                else:
                    await update.bot.send_message(
                        chat_id=update.from_user.id,
                        text="Отлично❤️ Загрузи 3 фотографии в хорошем качестве, где хорошо видно твое лицо. По желанию можно добавить 1 видео",
                        reply_markup=media_done_keyboard(),
                    )
                return
            if not robokassa_ready():
                await update.bot.send_message(
                    chat_id=update.from_user.id,
                    text="Сейчас оплата недоступна",
                )
                return
            description = "\n".join([
                "<b>В чем преимущество анонимного размещения:</b>",
                "",
                "Если ты не хочешь, чтобы кто-то из знакомых, клиентов и других людей узнал о твоей личной жизни - то этот формат для тебя❤️",
                "",
                "Никто не увидит твое имя и фото, только факты, которые укажешь в анкете",
                "",
                "Необходимо будет пройти верификацию по фото (это анонимно, увидим только мы)",
                "",
                "<b>Нам важно, чтобы здесь собирались только честные люди, которые серьезно настроены на отношения🥰</b>",
            ])
            await update.bot.send_message(
                chat_id=update.from_user.id,
                text=description,
                parse_mode="HTML",
            )
            invoice_id, pay_url = create_anonymous_profile_payment(
                user_id=update.from_user.id,
                amount_kopecks=ANONYMOUS_PROFILE_PRICE,
                description="Выставить анкету анонимно",
            )
            await update.bot.send_message(
                chat_id=update.from_user.id,
                text="Оплатите размещение в Robokassa и затем нажмите 'Проверить оплату'.",
                reply_markup=_anonymous_payment_keyboard(pay_url, invoice_id)
            )
            await state.update_data(anonymous_verification=False, anonymous_invoice_id=invoice_id)
        return

    current_state = await state.get_state()
    data = await state.get_data()
    if data.get("edit_mode") and current_state != ProfileStates.waiting_photo.state:
        edit_field = data.get("edit_field")
        user_id = update.from_user.id
        user = Store.user.get_by_user_id(user_id)
        if not user:
            await state.clear()
            return
        if current_state == ProfileStates.waiting_family.state and edit_field == "family":
            await update.answer("Выберите вариант кнопкой", reply_markup=family_status_keyboard())
            return
        if not update.text:
            await update.answer("Пожалуйста, отправьте текст.")
            return
        if current_state == ProfileStates.waiting_name.state and edit_field == "name":
            updated = _update_profile(user_id, name=update.text.strip())
            await _finalize_profile_edit(update, state, user_id, updated)
            return
        if current_state == ProfileStates.waiting_age.state and edit_field == "age":
            age = _parse_age(update.text)
            if age is None:
                await update.answer("Возраст должен быть числом.")
                return
            if age < 18:
                await update.answer("Вам должно быть 18+ для использования бота")
                return
            updated = _update_profile(user_id, age=age)
            await _finalize_profile_edit(update, state, user_id, updated)
            return
        if current_state == ProfileStates.waiting_city.state and edit_field == "city":
            city = await resolve_city(update.text)
            updated = _update_profile(user_id, city=city)
            await _finalize_profile_edit(update, state, user_id, updated)
            return
        if current_state == ProfileStates.waiting_about.state and edit_field == "about":
            answers = _parse_profile_text(user.text)
            answers["about"] = update.text
            new_text = _build_profile_text(
                answers["about"], answers["activity"], answers["partner"], answers["family"]
            )
            updated = _update_profile(user_id, text=new_text)
            await _finalize_profile_edit(update, state, user_id, updated)
            return
        if current_state == ProfileStates.waiting_activity.state and edit_field == "activity":
            answers = _parse_profile_text(user.text)
            answers["activity"] = update.text
            new_text = _build_profile_text(
                answers["about"], answers["activity"], answers["partner"], answers["family"]
            )
            updated = _update_profile(user_id, text=new_text)
            await _finalize_profile_edit(update, state, user_id, updated)
            return
        if current_state == ProfileStates.waiting_partner.state and edit_field == "partner":
            answers = _parse_profile_text(user.text)
            answers["partner"] = update.text
            new_text = _build_profile_text(
                answers["about"], answers["activity"], answers["partner"], answers["family"]
            )
            updated = _update_profile(user_id, text=new_text)
            await _finalize_profile_edit(update, state, user_id, updated)
            return

    if current_state == ProfileStates.waiting_name.state:
        await state.update_data(name=update.text)
        await state.set_state(ProfileStates.waiting_age)
        photo = FSInputFile("./assets/age.PNG")
        await update.bot.send_photo(
            chat_id=update.from_user.id,
            photo=photo,
            caption="Сколько тебе лет?",
        )
        return
    elif current_state == ProfileStates.waiting_age.state:
        age = _parse_age(update.text)
        if age is None:
            await update.answer("Возраст должен быть числом.")
            return
        if age < 18:
            await update.answer("Вам должно быть 18+ для использования бота")
            return
        await state.update_data(age=age)
        await state.set_state(ProfileStates.waiting_city)
        photo = FSInputFile("./assets/city.PNG")
        await update.bot.send_photo(
            chat_id=update.from_user.id,
            photo=photo,
            caption="В каком городе хочешь встретить любовь?",
        )
        return
    elif current_state == ProfileStates.waiting_city.state:
        city = await resolve_city(update.text)
        await state.update_data(city=city)
        await state.set_state(ProfileStates.waiting_about)
        await update.answer("<b>Осталось еще немного</b>❤️", parse_mode='HTML')
        photo = FSInputFile("./assets/about.PNG")
        await update.bot.send_photo(
            chat_id=update.from_user.id,
            photo=photo,
            caption="<b>Расскажи о себе:</b>\nКакая у тебя сфера деятельности?",
            parse_mode='HTML'
        )
        return
    elif current_state == ProfileStates.waiting_about.state:
        await state.update_data(about=update.text)
        await state.set_state(ProfileStates.waiting_activity)
        photo = FSInputFile("./assets/hobbies.PNG")
        await update.bot.send_photo(
            chat_id=update.from_user.id,
            photo=photo,
            caption="<b>Твои увлечения и хобби:</b>\n\nКак любишь проводить свободное время? Можно подробно рассказать: какие фильмы нравятся? Что интересно читать/изучать?",
            parse_mode='HTML'
        )
        return
    elif current_state == ProfileStates.waiting_activity.state:
        await state.update_data(activity=update.text)
        await state.set_state(ProfileStates.waiting_partner)
        photo = FSInputFile("./assets/parnter.PNG")
        await update.bot.send_photo(
            chat_id=update.from_user.id,
            photo=photo,
            caption="<b>Какого партнера видишь рядом с собой?</b> Опиши, что важно",
            parse_mode='HTML'
        )
        return
    elif current_state == ProfileStates.waiting_partner.state:
        data = await state.get_data()
        await state.update_data(partner=update.text)
        await state.set_state(ProfileStates.waiting_family)
        await update.bot.send_message(
            chat_id=update.from_user.id,
            text="Семейное положение:",
            reply_markup=family_status_keyboard(sex=data.get("sex")),
        )
        return
    elif current_state == ProfileStates.waiting_family.state:
        await update.answer("Выберите вариант кнопкой", reply_markup=family_status_keyboard())
    elif current_state == ProfileStates.waiting_sex.state:
        await update.answer("Укажи свой пол", reply_markup=sex_keyboard("sex"))
    elif current_state == ProfileStates.waiting_photo.state:
        if not update.photo:
            await update.answer("Пожалуйста, отправьте фото. После отправки нажмите кнопку «Готово».")
            return
        data = await state.get_data()
        media_ids = list(data.get("medias", []))
        media_ids.append(update.photo[-1].file_id)
        await state.update_data(medias=media_ids)
        await update.answer("Фото добавлено. Можно отправить еще или нажать «Готово».", reply_markup=media_done_keyboard())
