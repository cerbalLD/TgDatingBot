from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from config import (
    ROBOKASSA_IS_TEST,
    ROBOKASSA_MERCHANT_LOGIN,
    ROBOKASSA_PASSWORD_1,
    ROBOKASSA_PAYMENT_URL,
)
from robokassa.api import generate_payment_link
from store import Store


def robokassa_ready() -> bool:
    return bool(ROBOKASSA_MERCHANT_LOGIN and ROBOKASSA_PASSWORD_1)


def _amount_to_decimal_rub(amount_kopecks: int) -> Decimal:
    return (Decimal(amount_kopecks) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _next_invoice_id() -> int:
    # Millisecond timestamp gives compact unique invoice ids for current traffic level.
    invoice_id = int(datetime.utcnow().timestamp() * 1000)
    while Store.payment.get_by_invoice_id(invoice_id):
        invoice_id += 1
    return invoice_id


def create_subscription_payment(*, user_id: int, plan_days: int, amount_kopecks: int, description: str) -> tuple[int, str]:
    invoice_id = _next_invoice_id()
    amount_rub = _amount_to_decimal_rub(amount_kopecks)
    payment_url = generate_payment_link(
        merchant_login=ROBOKASSA_MERCHANT_LOGIN,
        merchant_password_1=ROBOKASSA_PASSWORD_1,
        cost=amount_rub,
        number=invoice_id,
        description=description,
        is_test=ROBOKASSA_IS_TEST,
        robokassa_payment_url=ROBOKASSA_PAYMENT_URL,
    )
    Store.payment.create(
        invoice_id=invoice_id,
        user_id=user_id,
        payment_type="subscription",
        payload=str(plan_days),
        amount=amount_kopecks,
        status=0,
        is_applied=False,
    )
    return invoice_id, payment_url


def create_anonymous_profile_payment(*, user_id: int, amount_kopecks: int, description: str) -> tuple[int, str]:
    invoice_id = _next_invoice_id()
    amount_rub = _amount_to_decimal_rub(amount_kopecks)
    payment_url = generate_payment_link(
        merchant_login=ROBOKASSA_MERCHANT_LOGIN,
        merchant_password_1=ROBOKASSA_PASSWORD_1,
        cost=amount_rub,
        number=invoice_id,
        description=description,
        is_test=ROBOKASSA_IS_TEST,
        robokassa_payment_url=ROBOKASSA_PAYMENT_URL,
    )
    Store.payment.create(
        invoice_id=invoice_id,
        user_id=user_id,
        payment_type="anonymous_profile",
        payload="",
        amount=amount_kopecks,
        status=0,
        is_applied=False,
    )
    return invoice_id, payment_url
