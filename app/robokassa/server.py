from aiohttp import web

from config import ROBOKASSA_PASSWORD_2, ROBOKASSA_RESULT_HOST, ROBOKASSA_RESULT_PATH, ROBOKASSA_RESULT_PORT
from robokassa.api import result_payment
from store import Store


async def _robokassa_result(request: web.Request) -> web.Response:
    inv_id = result_payment(ROBOKASSA_PASSWORD_2, str(request.url))
    if not inv_id:
        return web.Response(text="bad sign", status=400)

    try:
        invoice_id = int(inv_id)
    except ValueError:
        return web.Response(text="bad inv id", status=400)

    payment = Store.payment.get_by_invoice_id(invoice_id)
    if not payment:
        return web.Response(text=f"OK{invoice_id}")

    if payment.status != 1:
        Store.payment.update(payment.id, status=1)

    return web.Response(text=f"OK{invoice_id}")


async def _robokassa_success(request: web.Request) -> web.Response:
    return web.Response(text="Платеж получен. Вернитесь в Telegram и нажмите 'Проверить оплату'.")


async def _robokassa_fail(request: web.Request) -> web.Response:
    return web.Response(text="Платеж не завершен. Вы можете попробовать снова.")


async def start_result_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get(ROBOKASSA_RESULT_PATH, _robokassa_result)
    app.router.add_get("/robokassa/success", _robokassa_success)
    app.router.add_get("/robokassa/fail", _robokassa_fail)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=ROBOKASSA_RESULT_HOST, port=ROBOKASSA_RESULT_PORT)
    await site.start()
    return runner
