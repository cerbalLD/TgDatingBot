from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from store import Store
from telegram.user.keyboards.main_menu import main_menu, start_continue_keyboard

router = Router()

OFFER_LINK = "https://telegra.ph/PUBLICHNAYA-OFERTA-02-23-9"
DATA_POLICY_LINK = "https://telegra.ph/dfadsfsa-02-18"
MAILINGS_LINK = "https://telegra.ph/Soglasie-na-poluchenie-rassylok-02-19-24"
SOCIAL_PUBLICATION_LINK = "https://telegra.ph/Soglasie-na-publikaciyu-v-socialnyh-setyah-02-19"
SPECIAL_CATEGORIES_LINK = "https://telegra.ph/Soglasie-na-obrabotku-specialnyh-kategorij-personalnyh-dannyh-02-19"


def _docs_consents_text() -> str:
    return "\n".join(
        [
            "📋 <b>Прежде чем начать</b>",
            "Для работы сервиса ознакомься с документами и подтверди согласие:",
            "",
            "<b>Обязательно:</b>",
            f"<a href='{OFFER_LINK}'>Публичная Оферта</a>",
            f"<a href='{DATA_POLICY_LINK}'>Согласие на обработку персональных данных</a>",
            "",
            "<b>Добровольно (сервис работает и без этого):</b>",
            f"<a href='{MAILINGS_LINK}'>Согласие на получение рассылок</a>",
            f"<a href='{SOCIAL_PUBLICATION_LINK}'>Согласие на публикацию в социальных сетях</a>",
            "",
            f"<a href='{SPECIAL_CATEGORIES_LINK}'>Согласие на обработку специальных категорий персональных данных</a>"
        ]
    )


def _docs_consents_keyboard(
    required: bool = False,
    mailings: bool = False,
    social: bool = False,
) -> InlineKeyboardMarkup:
    req_icon = "✅" if required else "⬜"
    mailing_icon = "✅" if mailings else "🔔"
    social_icon = "✅" if social else "📱"
    r, m, s = int(required), int(mailings), int(social)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{req_icon} Принимаю обязательные условия",
                    callback_data=f"user:start:docs:toggle_required:{r}:{m}:{s}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{mailing_icon} Хочу рассылки",
                    callback_data=f"user:start:docs:toggle_mailings:{r}:{m}:{s}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{social_icon} Согласен на публикацию",
                    callback_data=f"user:start:docs:toggle_social:{r}:{m}:{s}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Продолжить",
                    callback_data=f"user:start:docs:continue:{r}:{m}:{s}",
                )
            ],
        ]
    )


async def show_main_menu(callback: CallbackQuery) -> None:
    user = Store.user.get_by_user_id(callback.from_user.id)
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=main_menu(user is not None, user.is_enabled if user else True),
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = Store.user.get_by_user_id(message.from_user.id)
    if user:
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu(True, user.is_enabled if user else True),
        )
        return
    await message.bot.send_video_note(
        chat_id=message.chat.id,
        video_note=FSInputFile("./assets/start_circle.mp4")
    )
    await message.bot.send_message(
        chat_id=message.chat.id,
        text="\n".join([
            "Добро пожаловать в проект 3 метра❤️",
            "",
            "Нажми «Продолжить», чтобы начать.",
        ]),
        parse_mode="HTML",
        reply_markup=start_continue_keyboard(),
    )


@router.callback_query(F.data == "user:start:continue")
async def cb_start_continue(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        _docs_consents_text(),
        parse_mode="HTML",
        reply_markup=_docs_consents_keyboard(),
    )


@router.callback_query(F.data.startswith("user:start:docs:"))
async def cb_start_docs(callback: CallbackQuery):
    _, _, _, action, required_raw, mailings_raw, social_raw = callback.data.split(":")
    required = bool(int(required_raw))
    mailings = bool(int(mailings_raw))
    social = bool(int(social_raw))

    if action == "toggle_required":
        required = not required
    elif action == "toggle_mailings":
        mailings = not mailings
    elif action == "toggle_social":
        social = not social
    elif action == "continue":
        if not required:
            await callback.answer("Нужно принять обязательные условия", show_alert=True)
            return
        await callback.answer()
        await show_main_menu(callback)
        return

    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=_docs_consents_keyboard(
            required=required,
            mailings=mailings,
            social=social,
        )
    )
