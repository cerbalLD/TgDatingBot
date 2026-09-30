from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import json
from pathlib import Path

from config import LIST_ADMIN_USER_ID
import config
from store import Store
from telegram.admin.states.admin import AdminManageStates

router = Router()


def _is_super_admin(user_id: int) -> bool:
    if isinstance(LIST_ADMIN_USER_ID, list):
        if user_id in LIST_ADMIN_USER_ID:
            return True
    elif user_id == LIST_ADMIN_USER_ID:
        return True
    admins = Store.admin.list(user_id=user_id, limit=1)
    return bool(admins and admins[0].level == 0)


@router.message(Command("addadmin"))
async def cmd_add_admin(message: Message, state: FSMContext):
    if not _is_super_admin(message.from_user.id):
        await message.answer("Недостаточно прав")
        return
    await state.set_state(AdminManageStates.waiting_add_contact)
    await message.answer("Отправьте контакт пользователя для добавления администратора")


@router.message(Command("deladmin"))
async def cmd_del_admin(message: Message, state: FSMContext):
    if not _is_super_admin(message.from_user.id):
        await message.answer("Недостаточно прав")
        return
    await state.set_state(AdminManageStates.waiting_remove_contact)
    await message.answer("Отправьте контакт администратора для удаления")


@router.message(Command("setadminlevel"))
async def cmd_set_admin_level(message: Message):
    if not _is_super_admin(message.from_user.id):
        await message.answer("Недостаточно прав")
        return
    parts = message.text.strip().split()
    if len(parts) != 3:
        await message.answer("Использование: /setadminlevel <user_id> <0|1>")
        return
    try:
        user_id = int(parts[1])
        level = int(parts[2])
    except ValueError:
        await message.answer("user_id и уровень должны быть числами")
        return
    if level not in (0, 1):
        await message.answer("Уровень может быть только 0 или 1")
        return
    if isinstance(LIST_ADMIN_USER_ID, list):
        is_super_admin = user_id in LIST_ADMIN_USER_ID
    else:
        is_super_admin = user_id == LIST_ADMIN_USER_ID
    if is_super_admin and level != 0:
        await message.answer("Нельзя менять уровень главного администратора")
        return

    admins = Store.admin.list(user_id=user_id, limit=1)
    if admins:
        Store.admin.update(admins[0].id, level=level)
    else:
        Store.admin.create(user_id=user_id, level=level)
    await message.answer("Уровень администратора обновлен")


@router.message(Command("setprice"))
async def cmd_set_price(message: Message):
    if not _is_super_admin(message.from_user.id):
        await message.answer("Недостаточно прав.")
        return
    parts = message.text.strip().split()
    if len(parts) != 3:
        await message.answer("Использование: /setprice <3|7|30> <цена в рублях>")
        return
    try:
        plan_id = int(parts[1])
        price_rub = int(parts[2])
    except ValueError:
        await message.answer("Цена и дни подписки должны быть числами.")
        return
    if plan_id not in (3, 7, 30):
        await message.answer("Длитель подписки может быть только 3, 7 или 30 дней.")
        return
    if price_rub <= 0:
        await message.answer("Цена подписки должна быть больше 0.")
        return

    price_kopecks = price_rub * 100
    config_path = Path(config.config_path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if plan_id == 3:
        data["subscription_price_3_days"] = price_kopecks
        config.SUBSCRIPTION_PRICE_3_DAYS = price_kopecks
    elif plan_id == 7:
        data["subscription_price_7_days"] = price_kopecks
        config.SUBSCRIPTION_PRICE_7_DAYS = price_kopecks
    else:
        data["subscription_price_30_days"] = price_kopecks
        config.SUBSCRIPTION_PRICE_30_DAYS = price_kopecks
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
    await message.answer(f"Цена подписки {plan_id} дня обновлена до {price_rub} рублей.")


@router.message(AdminManageStates.waiting_add_contact)
async def st_add_admin_contact(message: Message, state: FSMContext):
    if not _is_super_admin(message.from_user.id):
        await message.answer("Недостаточно прав")
        await state.clear()
        return
    if not message.contact or not message.contact.user_id:
        await message.answer("Нужно отправить контакт пользователя")
        return

    user_id = message.contact.user_id
    if isinstance(LIST_ADMIN_USER_ID, list):
        is_super_admin = user_id in LIST_ADMIN_USER_ID
    else:
        is_super_admin = user_id == LIST_ADMIN_USER_ID
    if is_super_admin:
        await message.answer("Удалить разработчика или владельца бота невозможно")
        await state.clear()
        return
    admins = Store.admin.list(user_id=user_id, limit=1)
    if admins:
        Store.admin.update(admins[0].id, level=1)
    else:
        Store.admin.create(user_id=user_id, level=1)

    await state.clear()
    await message.answer("Администратор добавлен")


@router.message(AdminManageStates.waiting_remove_contact)
async def st_remove_admin_contact(message: Message, state: FSMContext):
    if not _is_super_admin(message.from_user.id):
        await message.answer("Недостаточно прав")
        await state.clear()
        return
    if not message.contact or not message.contact.user_id:
        await message.answer("Нужно отправить контакт пользователя")
        return

    user_id = message.contact.user_id
    admins = Store.admin.list(user_id=user_id, limit=1)
    if not admins:
        await message.answer("Администратор не найден")
        await state.clear()
        return

    Store.admin.delete(admins[0].id)
    await state.clear()
    await message.answer("Администратор удален")
