from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from store import Store
from telegram.user.states.complaint import ComplaintStates

router = Router()


@router.callback_query(F.data == "user:main_menu:complaint")
async def cb_complaint(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ComplaintStates.waiting_message)
    await state.update_data(complaint_target_user_id=None)
    await state.update_data(complaint_type=0)
    await callback.message.answer(
        "Опишите проблему одним сообщением. Мы передадим ее модератору."
    )


@router.message(ComplaintStates.waiting_message)
async def st_complaint_message(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("complaint_target_user_id")
    complaint_type = data.get("complaint_type", 0)
    Store.complaint.create(
        user_id=message.from_user.id,
        user_message_id=message.message_id,
        target_user_id=target_user_id,
        complaint_type=complaint_type,
        status=0,
    )
    await state.clear()
    await message.answer(
        "Жалоба отправлена. Модератор ответит вам в этом чате."
    )

@router.callback_query(F.data.startswith("user:complaint:profile:"))
async def cb_profile_complaint(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        target_user_id = int(callback.data.split(":")[-1])
    except ValueError:
        target_user_id = None
    await state.set_state(ComplaintStates.waiting_message)
    await state.update_data(complaint_target_user_id=target_user_id)
    await state.update_data(complaint_type=1)
    await callback.message.answer(
        "Опишите проблему одним сообщением"
    )

