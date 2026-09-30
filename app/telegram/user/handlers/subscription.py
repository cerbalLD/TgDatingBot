from datetime import datetime, timedelta
import math

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    SUBSCRIPTION_PRICE_3_DAYS,
    SUBSCRIPTION_PRICE_7_DAYS,
    SUBSCRIPTION_PRICE_30_DAYS,
)
from robokassa.service import create_subscription_payment, robokassa_ready
from store import Store
from telegram.user.keyboards.subscription import subscription_keyboard

router = Router()

SUBSCRIPTION_PLANS = {
    3: {
        "title": "3 дня",
        "description": "пробный период на 3 дня чтобы попробовать возможности",
        "price": SUBSCRIPTION_PRICE_3_DAYS,
        "days": 3,
    },
    7: {
        "title": "7 дней",
        "description": "продление подписки на 7 дней",
        "price": SUBSCRIPTION_PRICE_7_DAYS,
        "days": 7,
    },
    30: {
        "title": "30 дней",
        "description": "продление подписки на 30 дней",
        "price": SUBSCRIPTION_PRICE_30_DAYS,
        "days": 30,
    },
}


def _build_subscription_text(user) -> str:
    now = datetime.utcnow()
    expires = user.expire_subscription_date
    if not expires or expires <= now:
        return "\n".join([
            "По подписке 3 метра PRO вы получаете полный пакет возможностей для максимального успеха в поиске своей любви❤️",
            "",
            "Эксклюзивные возможности:",
            "",
            "❤️Неограниченный просмотр анкет",
            "❤️ Просмотр всех поставленных лайков от других участников",
            "",
            "С подпиской 3 метра PRO шансы встретить свою судьбу повышаются",
            "",
            "Тарифы:",
        ])
    days_left = max(0, math.ceil((expires - now).total_seconds() / 86400))
    return "\n".join([
        f"Дата окончания: {expires:%Y-%m-%d %H:%M}",
        f"Осталось дней: {days_left}",
    ])


def _apply_subscription(user_id: int, plan_id: int) -> bool:
    user = Store.user.get_by_user_id(user_id)
    if not user:
        return False

    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        return False

    now = datetime.utcnow()
    expires = user.expire_subscription_date
    base = expires if expires and expires > now else now
    new_expires = base + timedelta(days=plan["days"])
    Store.user.update(user.id, expire_subscription_date=new_expires, subscriptions=plan_id)
    return True


def _robokassa_payment_keyboard(url: str, invoice_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить в Robokassa", url=url)],
            [InlineKeyboardButton(text="Проверить оплату", callback_data=f"user:subscription:check:{invoice_id}")],
        ]
    )


@router.callback_query(F.data == "user:main_menu:paysub")
async def cb_subscription(callback: CallbackQuery):
    await callback.answer()
    user = Store.user.get_by_user_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала создайте анкету")
        return

    price_3_rub = SUBSCRIPTION_PRICE_3_DAYS // 100
    price_7_rub = SUBSCRIPTION_PRICE_7_DAYS // 100
    price_30_rub = SUBSCRIPTION_PRICE_30_DAYS // 100
    await callback.message.answer(
        _build_subscription_text(user),
        reply_markup=subscription_keyboard(price_3_rub, price_7_rub, price_30_rub),
    )


@router.callback_query(F.data.startswith("user:subscription:buy:"))
async def cb_buy_subscription(callback: CallbackQuery):
    await callback.answer()
    user = Store.user.get_by_user_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала создайте анкету")
        return

    try:
        plan_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.message.answer("Что-то пошло не так, обратитесь к администратору")
        return

    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        await callback.message.answer("Такого тарифа больше нет")
        return

    if not robokassa_ready():
        await callback.message.answer("Оплата временно недоступна")
        return

    invoice_id, pay_url = create_subscription_payment(
        user_id=callback.from_user.id,
        plan_days=plan_id,
        amount_kopecks=plan["price"],
        description=f"Подписка {plan['title']}",
    )

    await callback.message.answer(
        "Перейдите к оплате в Robokassa и после оплаты нажмите 'Проверить оплату'.",
        reply_markup=_robokassa_payment_keyboard(pay_url, invoice_id),
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data.startswith("user:subscription:check:"))
async def cb_check_subscription_payment(callback: CallbackQuery):
    await callback.answer()
    try:
        invoice_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.message.answer("Некорректный номер платежа")
        return

    payment = Store.payment.get_by_invoice_id(invoice_id)
    if not payment or payment.user_id != callback.from_user.id or payment.payment_type != "subscription":
        await callback.message.answer("Платеж не найден")
        return

    if payment.status != 1:
        await callback.message.answer("Платеж еще не подтвержден. Если вы оплатили только что, подождите 10-30 секунд и проверьте снова.")
        return

    if not payment.is_applied:
        try:
            plan_id = int(payment.payload)
        except (TypeError, ValueError):
            await callback.message.answer("Ошибка данных платежа")
            return

        if not _apply_subscription(callback.from_user.id, plan_id):
            await callback.message.answer("Не удалось активировать подписку")
            return

        Store.payment.update(payment.id, is_applied=True)

    await callback.message.answer("Подписка активирована")
    price_3_rub = SUBSCRIPTION_PRICE_3_DAYS // 100
    price_7_rub = SUBSCRIPTION_PRICE_7_DAYS // 100
    price_30_rub = SUBSCRIPTION_PRICE_30_DAYS // 100
    await callback.message.answer(
        _build_subscription_text(Store.user.get_by_user_id(callback.from_user.id)),
        reply_markup=subscription_keyboard(price_3_rub, price_7_rub, price_30_rub),
    )
